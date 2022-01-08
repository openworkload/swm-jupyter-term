from dataclasses import dataclass

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
        <label for='it-item-{{ it.name }}' class='form-control input-group'>
            <div class='col-md-1'>
                <input type='radio' name='it' id='it-item-{{ it.name }}' value='{{ it.flavor_name }}'/>
            </div>
            <div class='col-md-11'>
                <strong>{{ it.remote_name }} ${{ it.price }}</strong>
            </div>
            <div class='col-md-9'>
                (
                {% for res in it.resources %}
                    {{ res.name }}={{ res.count }}
                {% endfor %}
                )
            </div>
        </label>
        {% endfor %}
        </div>
        """

    def _get_instance_types(self, swm_api: SwmApi) -> list[InstanceType]:
        instance_types: list[InstanceType] = []
        remote_sites = swm_api.get_remote_sites()
        flavors = swm_api.get_flavors()
        for flavor in flavors:
            remote = next(remote_site for remote_site in remote_sites if flavor.remote_id == remote_site.id)
            instance_type = InstanceType(remote.name, flavor.name, flavor.price, flavor.resources)
            instance_types.append(instance_type)
        return instance_types

    def render(self, swm_api: SwmApi) -> str:
        html_form = Environment(loader=BaseLoader).from_string(self._template)  # type: ignore
        instance_types = self._get_instance_types(swm_api)
        return html_form.render(instance_types=instance_types)
