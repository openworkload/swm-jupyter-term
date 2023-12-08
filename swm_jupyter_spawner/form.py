from dataclasses import dataclass
from logging import Logger
import typing
import os

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
            providers.setdefault(remote_name, Provider(name=remote_name, instance_types=[]))
            providers[remote_name].instance_types.append(instance_type)
        return providers

    def render(self, swm_api: SwmApi) -> str:
        with open(os.path.dirname(__file__) + '/form.html.jinja') as _file:
            html_form = Template(_file.read())
        providers = self._get_providers(swm_api)
        return html_form.render(providers=providers)

    def get_options(self, form_data: typing.Dict[str, list[str]], spool_dir: str) -> typing.Dict[str, typing.Any]:
        options: typing.Dict[str, typing.Any] = {}
        options['input_files'] = self._save_tmp_input_files(form_data.get('files[]_file', []), spool_dir)
        options['flavor'] = form_data['it'][0]
        self.log.debug(f"Parsed options: {options}")
        return options

    def _save_tmp_input_files(self, form_files: list[dict[str, bytes|str]], spool_dir:str) -> list[str]:
        result: list[str] = []
        if form_files:
            for file_info in form_files:
                filename = file_info['filename']
                content = file_info['body']
                file_path = spool_dir + "/" + filename
                self.log.debug(f"Save input temporary file: {file_path}, {len(content)}")
                open(file_path, 'wb').write(content)
                result.append(file_path)
        return result
