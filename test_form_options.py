"""Spawn-form values must not inject #SWM directives (issue 30)."""

from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateError, select_autoescape

from swmjupyter.form import SwmForm
from swmjupyter.form_options import (
    FormOptionError,
    sanitize_cloud_image,
    sanitize_flavor,
    sanitize_gpus,
    swm_directive_token,
)


class TestSanitizeFlavor(unittest.TestCase):
    def test_accepts_common_names(self) -> None:
        self.assertEqual(sanitize_flavor("m1.small"), "m1.small")
        self.assertEqual(sanitize_flavor("Standard_D2_v4"), "Standard_D2_v4")
        self.assertEqual(sanitize_flavor(b"m1.medium"), "m1.medium")

    def test_rejects_injection(self) -> None:
        with self.assertRaises(FormOptionError):
            sanitize_flavor("m1.small\n#SWM account evil")
        with self.assertRaises(FormOptionError):
            sanitize_flavor("m1.small\r\n#SWM account evil")
        with self.assertRaises(FormOptionError):
            sanitize_flavor("foo #SWM bar")
        with self.assertRaises(FormOptionError):
            sanitize_flavor("has space")
        with self.assertRaises(FormOptionError):
            sanitize_flavor("")
        with self.assertRaises(FormOptionError):
            sanitize_flavor("x" * 200)


class TestSanitizeGpus(unittest.TestCase):
    def test_accepts_digits(self) -> None:
        self.assertEqual(sanitize_gpus("0"), "0")
        self.assertEqual(sanitize_gpus("8"), "8")

    def test_rejects_bad(self) -> None:
        with self.assertRaises(FormOptionError):
            sanitize_gpus("1\n#SWM gpus 99")
        with self.assertRaises(FormOptionError):
            sanitize_gpus("-1")
        with self.assertRaises(FormOptionError):
            sanitize_gpus("abc")


class TestSanitizeCloudImage(unittest.TestCase):
    def test_accepts_names(self) -> None:
        self.assertEqual(sanitize_cloud_image("ubuntu"), "ubuntu")
        self.assertEqual(sanitize_cloud_image("ubuntu-hpc/2404"), "ubuntu-hpc/2404")

    def test_rejects_injection(self) -> None:
        with self.assertRaises(FormOptionError):
            sanitize_cloud_image("ubuntu\n#SWM account evil")
        with self.assertRaises(FormOptionError):
            sanitize_cloud_image("bad;#SWM")


class TestGetOptionsRejectsInjection(unittest.TestCase):
    def test_forged_flavor_raises(self) -> None:
        form = SwmForm(logging.getLogger("test"))
        with tempfile.TemporaryDirectory() as spool:
            form_data = {
                "selected_flavor_name": ["ok\n#SWM account evil"],
                "selected_flavor_gpus": ["0"],
                "selected_cloud_image_name": ["ubuntu"],
            }
            with self.assertRaises(FormOptionError):
                form.get_options(form_data, spool)  # type: ignore[arg-type]

    def test_happy_path(self) -> None:
        form = SwmForm(logging.getLogger("test"))
        with tempfile.TemporaryDirectory() as spool:
            form_data = {
                "selected_flavor_name": ["m1.small"],
                "selected_flavor_gpus": ["0"],
                "selected_cloud_image_name": ["ubuntu-hpc/2404"],
            }
            options = form.get_options(form_data, spool)  # type: ignore[arg-type]
            self.assertEqual(options["flavor"], "m1.small")
            self.assertEqual(options["gpus"], "0")
            self.assertEqual(options["cloud-image"], "ubuntu-hpc/2404")


class TestSwmTokenJinjaFilter(unittest.TestCase):
    def test_render_rejects_bad_token(self) -> None:
        env = Environment(
            loader=FileSystemLoader(str(Path(__file__).resolve().parent / "swmjupyter")),
            autoescape=select_autoescape(enabled_extensions=()),
        )
        env.filters["swm_token"] = swm_directive_token
        template = env.get_template("job.sh.jinja")
        job_info = {
            "account": "openstack",
            "container_registry": "swmregistry.azurecr.io",
            "container_image_name": "jupyter/pytorch-notebook",
            "server_port": 8888,
            "container_image_tag": "tag",
            "cloud_image_name": "ubuntu",
            "flavor": "m1.small\n#SWM account evil",
            "gpus": "0",
            "ports": "8888/tcp/in",
            "jupyterhub_client_id": "id",
            "hub_url": "http://localhost/hub/api",
            "service_scheme": "http",
            "internal_ssl": False,
            "ssl_key_file": "jupyterhub_ssl_key.pem",
            "ssl_cert_file": "jupyterhub_ssl_cert.pem",
            "ssl_ca_file": "jupyterhub_ssl_ca.pem",
            "input_files": [],
            "output_files": [],
            "storage": "store",
        }
        with self.assertRaises((FormOptionError, TemplateError)):
            template.render(job_info=job_info)

    def test_render_ok(self) -> None:
        env = Environment(
            loader=FileSystemLoader(str(Path(__file__).resolve().parent / "swmjupyter")),
            autoescape=select_autoescape(enabled_extensions=()),
        )
        env.filters["swm_token"] = swm_directive_token
        rendered = env.get_template("job.sh.jinja").render(
            job_info={
                "account": "openstack",
                "container_registry": "reg",
                "container_image_name": "img",
                "server_port": 8888,
                "container_image_tag": "tag",
                "cloud_image_name": "ubuntu",
                "flavor": "m1.small",
                "gpus": "0",
                "ports": "8888/tcp/in",
                "jupyterhub_client_id": "id",
                "hub_url": "http://localhost/hub/api",
                "service_scheme": "http",
                "internal_ssl": False,
                "ssl_key_file": "jupyterhub_ssl_key.pem",
                "ssl_cert_file": "jupyterhub_ssl_cert.pem",
                "ssl_ca_file": "jupyterhub_ssl_ca.pem",
                "input_files": [],
                "output_files": [],
                "storage": "store",
            }
        )
        self.assertIn("#SWM flavor m1.small", rendered)
        self.assertNotIn("#SWM account evil", rendered)


if __name__ == "__main__":
    unittest.main()
