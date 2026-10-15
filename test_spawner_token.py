"""Hub API token must not appear in the submitted job script (issue 29)."""

from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from jinja2 import Environment, FileSystemLoader, select_autoescape

from swmjupyter.form_options import swm_directive_token
from swmjupyter.spawner import (
    HUB_API_TOKEN_FILENAME,
    summarize_job_script_for_log,
    write_hub_api_token_file,
)


SECRET = "test-secret-token-xyz"


class TestWriteHubApiTokenFile(unittest.TestCase):
    def test_creates_mode_0600_file(self) -> None:
        with tempfile.TemporaryDirectory() as spool:
            path = write_hub_api_token_file(spool, SECRET)
            self.assertEqual(os.path.basename(path), HUB_API_TOKEN_FILENAME)
            self.assertTrue(os.path.isfile(path))
            mode = stat.S_IMODE(os.stat(path).st_mode)
            self.assertEqual(mode, 0o600)
            self.assertEqual(Path(path).read_text(encoding="utf-8"), SECRET)


class TestSummarizeJobScriptForLog(unittest.TestCase):
    def test_redacts_token(self) -> None:
        script = f"export FOO=1\nexport JUPYTERHUB_API_TOKEN={SECRET}\n"
        summary = summarize_job_script_for_log(script, SECRET)
        self.assertNotIn(SECRET, summary)
        self.assertIn("***", summary)
        self.assertIn(f"{len(script)} bytes", summary)


class TestJobScriptTemplateNoToken(unittest.TestCase):
    def test_template_reads_token_from_file(self) -> None:
        template_path = Path(__file__).resolve().parent / "swmjupyter" / "job.sh.jinja"
        job_info = {
            "account": "openstack",
            "container_registry": "swmregistry.azurecr.io",
            "container_image_name": "jupyter/pytorch-notebook",
            "server_port": 8888,
            "container_image_tag": "cuda12-hub-5.2.1",
            "cloud_image_name": "ubuntu",
            "flavor": "m1.small",
            "gpus": "0",
            "ports": "8888/tcp/in,8081/tcp/out",
            "jupyterhub_client_id": "jupyterhub-user-alice",
            "hub_url": "http://localhost:8081/hub/api",
            "service_scheme": "http",
            "internal_ssl": False,
            "ssl_key_file": "jupyterhub_ssl_key.pem",
            "ssl_cert_file": "jupyterhub_ssl_cert.pem",
            "ssl_ca_file": "jupyterhub_ssl_ca.pem",
            "input_files": ["/tmp/spool/jupyterhub_api_token"],
            "output_files": [],
            "storage": "swmblobcontainer",
        }
        env = Environment(
            loader=FileSystemLoader(str(template_path.parent)),
            autoescape=select_autoescape(enabled_extensions=()),
        )
        env.filters["swm_token"] = swm_directive_token
        rendered = env.get_template(template_path.name).render(job_info=job_info)
        self.assertNotIn(SECRET, rendered)
        self.assertNotIn(f"JUPYTERHUB_API_TOKEN={SECRET}", rendered)
        self.assertNotRegex(rendered, r"export JUPYTERHUB_API_TOKEN=[^\s$]+")
        self.assertIn('TOKEN_FILE=jupyterhub_api_token', rendered)
        self.assertIn('export JUPYTERHUB_API_TOKEN=$(cat "$TOKEN_FILE")', rendered)
        self.assertIn('rm -f "$TOKEN_FILE"', rendered)
        self.assertIn("#SWM input-files /tmp/spool/jupyterhub_api_token", rendered)


class TestRenderJobScriptIntegration(unittest.TestCase):
    def test_render_writes_token_file_and_omits_secret(self) -> None:
        from swmjupyter.spawner import SwmSpawner

        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "jupyter-spawner.conf")
            Path(config_path).write_text("account=test\n", encoding="utf-8")
            spool_parent = os.path.join(tmp, "uploads")
            os.makedirs(spool_parent, mode=0o700)

            with patch.object(SwmSpawner, "__init__", lambda self, *a, **k: None):
                spawner = SwmSpawner.__new__(SwmSpawner)
            spawner.log = MagicMock()
            spawner._config_file = config_path
            spawner._config = {"account": "test"}
            spawner._jupyterhub_port = 8081
            spawner._jupyterhub_host = "localhost"
            spawner._jupyter_singleuser_port = 8888
            spawner._spool_dir = tempfile.TemporaryDirectory(prefix=".swmjupyter_", dir=spool_parent)
            spawner.internal_ssl = False
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
                    "JUPYTERHUB_API_TOKEN": SECRET,
                    "JUPYTERHUB_CLIENT_ID": "jupyterhub-user-alice",
                }
            )
            try:
                script = spawner._render_job_script()
            finally:
                spawner._spool_dir.cleanup()

            self.assertNotIn(SECRET, script)
            self.assertNotIn(f"JUPYTERHUB_API_TOKEN={SECRET}", script)
            self.assertIn("export JUPYTERHUB_API_TOKEN=$(cat \"$TOKEN_FILE\")", script)
            # Token was written then spool cleaned; check log was called with redacted summary
            logged = " ".join(str(c) for c in spawner.log.info.call_args_list)
            self.assertNotIn(SECRET, logged)
            self.assertIn("bytes", logged)


if __name__ == "__main__":
    unittest.main()
