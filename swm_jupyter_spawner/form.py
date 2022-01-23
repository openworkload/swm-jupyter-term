from dataclasses import dataclass
from logging import Logger
import typing

from jinja2 import BaseLoader, Environment
from swmclient.api import SwmApi
from swmclient.generated.models.resource import Resource


@dataclass
class InstanceType:
    remote_name: str
    flavor_name: str
    price: float
    resources: list[Resource]


class SwmForm:

    _template = """
        <style>
        #swm-instance-type-list label p {
            font-weight: normal;
        }
        </style>
        <div class='form-group' id='swm-instance-type-list'>
        {% for it in instance_types %}
        <label for='it-item-{{ it.flavor_name }}' class='form-control input-group'>
            <div class='col-md-1'>
                <input type='radio' name='it' id='it-item-{{ it.flavor_name }}' value='{{ it.flavor_name }}'/>
            </div>
            <div class='col-md-11'>
                <strong>{{ it.flavor_name }}: ${{ it.price }}, {{ it.remote_name }}, </strong>
                {% for res in it.resources %}
                    {{ res.name }}={{ res.count }}
                {% endfor %}
            </div>
        </label>
        {% endfor %}
        </div>
        """

    def __init__(self, logger: Logger) -> None:
        self.log = logger

    def _get_instance_types(self, swm_api: SwmApi) -> list[InstanceType]:
        instance_types: list[InstanceType] = []
        remote_sites = swm_api.get_remote_sites()
        flavors = swm_api.get_flavors()
        for flavor in flavors:
            if flavor.remote_id:
                remote = next(remote_site for remote_site in remote_sites if flavor.remote_id == remote_site.id)
                remote_name = remote.name
            else:
                remote_name = "-"
            instance_type = InstanceType(remote_name, flavor.name, flavor.price, flavor.resources)
            instance_types.append(instance_type)
        return instance_types

    def render(self, swm_api: SwmApi) -> str:
        html_form = Environment(loader=BaseLoader).from_string(self._template)  # type: ignore
        instance_types = self._get_instance_types(swm_api)
        return html_form.render(instance_types=instance_types)

    def get_options(self, form_data: typing.Dict[str, list[str]]) -> typing.Dict[str, typing.Any]:
        self.log.info(f"Form data: {form_data}")
        options: typing.Dict[str, typing.Any] = {}
        options['flavor'] = form_data['it'][0]
        return options
