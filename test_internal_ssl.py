"""Hub↔singleuser internal SSL (issue 32)."""

from __future__ import annotations

import os
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from jinja2 import Environment, FileSystemLoader, select_autoescape

from swmjupyter.form_options import swm_directive_token
from swmjupyter.hub_security import HubSecurityError, resolve_hub_security, resolve_internal_ssl
from swmjupyter.spawner import (
    SSL_CA_FILENAME,
    SSL_CERT_FILENAME,
    SSL_KEY_FILENAME,
    stage_ssl_file,
)
from swmjupyter.tcp_forward import LocalTcpForward


class TestResolveInternalSsl(unittest.TestCase):
    def test_default_on(self) -> None:
        self.assertTrue(resolve_internal_ssl({}, "127.0.0.1"))
        self.assertTrue(resolve_hub_security({}).internal_ssl)

    def test_explicit_on(self) -> None:
        self.assertTrue(resolve_internal_ssl({"SWM_JUPYTER_INTERNAL_SSL": "1"}, "0.0.0.0"))

    def test_off_loopback_allowed(self) -> None:
        self.assertFalse(resolve_internal_ssl({"SWM_JUPYTER_INTERNAL_SSL": "0"}, "127.0.0.1"))
        settings = resolve_hub_security(
            {"SWM_JUPYTER_INTERNAL_SSL": "0", "SWM_JUPYTER_BIND_IP": "127.0.0.1"}
        )
        self.assertFalse(settings.internal_ssl)

    def test_off_non_loopback_rejected(self) -> None:
        with self.assertRaises(HubSecurityError) as ctx:
            resolve_hub_security(
                {"SWM_JUPYTER_INTERNAL_SSL": "0", "SWM_JUPYTER_BIND_IP": "0.0.0.0"}
            )
        self.assertIn("loopback", str(ctx.exception).lower())

    def test_trusted_alt_names_include_connect_host(self) -> None:
        settings = resolve_hub_security({"SWM_JUPYTER_HUB_CONNECT_HOST": "hub.example.org"})
        self.assertIn("DNS:hub.example.org", settings.trusted_alt_names)
        self.assertIn("DNS:localhost", settings.trusted_alt_names)


class TestStageSslFile(unittest.TestCase):
    def test_copies_with_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "src.pem")
            Path(src).write_text("KEY", encoding="utf-8")
            spool = os.path.join(tmp, "spool")
            os.makedirs(spool)
            dest = stage_ssl_file(spool, src, SSL_KEY_FILENAME, 0o600)
            self.assertEqual(os.path.basename(dest), SSL_KEY_FILENAME)
            self.assertEqual(Path(dest).read_text(encoding="utf-8"), "KEY")
            self.assertEqual(os.stat(dest).st_mode & 0o777, 0o600)


class TestJobScriptInternalSsl(unittest.TestCase):
    def _render(self, internal_ssl: bool) -> str:
        template_path = Path(__file__).resolve().parent / "swmjupyter" / "job.sh.jinja"
        scheme = "https" if internal_ssl else "http"
        job_info = {
            "account": "openstack",
            "container_registry": "swmregistry.azurecr.io",
            "container_image_name": "jupyter/pytorch-notebook",
            "server_port": 8888,
            "container_image_tag": "tag",
            "cloud_image_name": "ubuntu",
            "flavor": "m1.small",
            "gpus": "0",
            "ports": "8888/tcp/in,8081/tcp/out",
            "jupyterhub_client_id": "jupyterhub-user-alice",
            "hub_url": f"{scheme}://localhost:8081/hub/api",
            "service_scheme": scheme,
            "internal_ssl": internal_ssl,
            "ssl_key_file": SSL_KEY_FILENAME,
            "ssl_cert_file": SSL_CERT_FILENAME,
            "ssl_ca_file": SSL_CA_FILENAME,
            "input_files": [
                "/tmp/spool/jupyterhub_api_token",
                f"/tmp/spool/{SSL_KEY_FILENAME}",
                f"/tmp/spool/{SSL_CERT_FILENAME}",
                f"/tmp/spool/{SSL_CA_FILENAME}",
            ],
            "output_files": [],
            "storage": "swmblobcontainer",
        }
        env = Environment(
            loader=FileSystemLoader(str(template_path.parent)),
            autoescape=select_autoescape(enabled_extensions=()),
        )
        env.filters["swm_token"] = swm_directive_token
        return env.get_template(template_path.name).render(job_info=job_info)

    def test_https_exports_ssl_env(self) -> None:
        rendered = self._render(True)
        self.assertIn("export JUPYTERHUB_API_URL=https://localhost:8081/hub/api", rendered)
        self.assertIn("export JUPYTERHUB_SERVICE_URL=https://0.0.0.0:8888", rendered)
        self.assertIn("export JUPYTERHUB_SSL_KEYFILE=", rendered)
        self.assertIn("export JUPYTERHUB_SSL_CERTFILE=", rendered)
        self.assertIn("export JUPYTERHUB_SSL_CLIENT_CA=", rendered)
        self.assertIn(SSL_KEY_FILENAME, rendered)

    def test_http_omits_ssl_env(self) -> None:
        rendered = self._render(False)
        self.assertIn("export JUPYTERHUB_SERVICE_URL=http://0.0.0.0:8888", rendered)
        self.assertNotIn("JUPYTERHUB_SSL_KEYFILE", rendered)


class TestMoveCertsAndRender(unittest.TestCase):
    def test_move_certs_stages_and_render_includes_files(self) -> None:
        from swmjupyter.spawner import SwmSpawner

        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "jupyter-spawner.conf")
            Path(config_path).write_text("account=test\n", encoding="utf-8")
            spool_parent = os.path.join(tmp, "uploads")
            os.makedirs(spool_parent, mode=0o700)
            src_dir = os.path.join(tmp, "certs")
            os.makedirs(src_dir)
            paths = {}
            for name, content in (("key.pem", "k"), ("cert.pem", "c"), ("ca.pem", "a")):
                p = os.path.join(src_dir, name)
                Path(p).write_text(content, encoding="utf-8")
                paths[{"key.pem": "keyfile", "cert.pem": "certfile", "ca.pem": "cafile"}[name]] = p

            with patch.object(SwmSpawner, "__init__", lambda self, *a, **k: None):
                spawner = SwmSpawner.__new__(SwmSpawner)
            spawner.log = MagicMock()
            spawner.user = MagicMock(name="alice")
            spawner.user.name = "alice"
            spawner._config_file = config_path
            spawner._config = {"account": "test"}
            spawner._jupyterhub_port = 8081
            spawner._jupyterhub_host = "hub.example.org"
            spawner._jupyter_singleuser_port = 8888
            spawner._spool_dir = tempfile.TemporaryDirectory(prefix=".swmjupyter_", dir=spool_parent)
            spawner.internal_ssl = True
            spawner._staged_ssl_paths = {}
            spawner.user_options = {
                "cloud-image": "ubuntu",
                "flavor": "m1.small",
                "gpus": "0",
                "input_files": [],
                "output_files": [],
            }
            spawner.get_env = MagicMock(
                return_value={
                    "JUPYTERHUB_API_TOKEN": "test-secret-token-xyz-issue32",
                    "JUPYTERHUB_CLIENT_ID": "jupyterhub-user-alice",
                }
            )
            try:
                import asyncio

                staged = asyncio.run(spawner.move_certs(paths))
                self.assertEqual(os.path.basename(staged["keyfile"]), SSL_KEY_FILENAME)
                script = spawner._render_job_script()
            finally:
                spawner._spool_dir.cleanup()

            self.assertIn("https://hub.example.org:8081/hub/api", script)
            self.assertIn("JUPYTERHUB_SSL_KEYFILE", script)
            self.assertIn(SSL_KEY_FILENAME, script)
            self.assertIn(SSL_CERT_FILENAME, script)
            self.assertIn(SSL_CA_FILENAME, script)


class TestLocalTcpForward(unittest.TestCase):
    def test_relays_bytes(self) -> None:
        backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backend.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        backend.bind(("127.0.0.1", 0))
        backend.listen(1)
        backend_port = backend.getsockname()[1]

        def accept_once() -> None:
            conn, _ = backend.accept()
            data = conn.recv(1024)
            conn.sendall(b"echo:" + data)
            conn.close()

        acceptor = threading.Thread(target=accept_once, daemon=True)
        acceptor.start()

        forward = LocalTcpForward("127.0.0.1", backend_port)
        local_port = forward.start()
        try:
            client = socket.create_connection(("127.0.0.1", local_port), timeout=5.0)
            client.sendall(b"ping")
            reply = client.recv(1024)
            client.close()
            self.assertEqual(reply, b"echo:ping")
        finally:
            forward.stop()
            backend.close()
            acceptor.join(timeout=2.0)


if __name__ == "__main__":
    unittest.main()
