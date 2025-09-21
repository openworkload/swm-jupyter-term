import os
import typing
from dataclasses import dataclass
from logging import Logger

from jinja2 import Template
from swmclient.api import SwmApi
from swmclient.generated.models.resource import Resource


@dataclass
class InstanceType:
    flavor_name: str
    price: float
    resources: list[Resource]


@dataclass
class Provider:
    name: str
    instance_types: list[InstanceType]
    vm_images: list[str]


class SwmForm:
    def __init__(self, logger: Logger) -> None:
        self.log = logger

    def _get_providers(self, swm_api: SwmApi) -> dict[str, Provider]:
        providers: dict[str, Provider] = {}
        remote_sites = swm_api.get_remote_sites()
        for flavor in swm_api.get_flavors():
            if flavor.remote_id:
                remote = next(remote_site for remote_site in remote_sites if flavor.remote_id == remote_site.id)
                remote_name = remote.name
            else:
                remote_name = "Other"
            instance_type = InstanceType(flavor.name, flavor.price, flavor.resources)
            providers.setdefault(remote_name, Provider(name=remote_name, instance_types=[], vm_images=[]))
            providers[remote_name].instance_types.append(instance_type)

        for image in swm_api.get_images():
            if image.remote_id:
                remote = next(remote_site for remote_site in remote_sites if image.remote_id == remote_site.id)
                remote_name = remote.name
                providers[remote_name].vm_images.append(image.name)

        return providers

    def render(self, swm_api: SwmApi) -> str:
        with open(os.path.dirname(__file__) + "/form.html.jinja") as _file:
            html_form = Template(_file.read())
        providers = self._get_providers(swm_api)
        return html_form.render(providers=providers)

    def get_options(self, form_data: dict[str, list[dict[str, bytes]]], spool_dir: str) -> dict[str, typing.Any]:
        options: dict[str, typing.Any] = {}
        input_files: list[dict[str, bytes]] = form_data.get("files[]_file", [])
        options["input_files"] = self._save_tmp_input_files(input_files, spool_dir)
        options["output_files"] = [os.path.basename(file_path) for file_path in options["input_files"]]
        options["flavor"] = form_data["selected_flavor_name"][0]
        options["gpus"] = form_data["selected_flavor_gpus"][0]
        options["cloud-image"] = form_data["selected_cloud_image_name"][0]
        self.log.debug(f"Parsed options: {options}")
        return options

    def _save_tmp_input_files(self, form_files: list[dict[str, bytes]], spool_dir: str) -> list[str]:
        result: list[str] = []
        if form_files:
            for file_info in form_files:
                filename = file_info["filename"]
                content = file_info["body"]
                file_path: str = spool_dir + "/" + str(filename)
                self.log.debug(f"Save input temporary file: {file_path}, {len(content)}")
                open(file_path, "wb").write(content)
                result.append(file_path)
        return result
