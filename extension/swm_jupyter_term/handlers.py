import json
import platform
import httpx

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
from swmclient.api import SwmApi
from swmclient.generated.types import File
import tornado

class RouteHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        url = f"https://{platform.node()}:8443"
        swm_api = SwmApi(
            url=url,
            key_file="~/.swm/key.pem",
            cert_file="~/.swm/cert.pem",
            ca_file="~/.swm/spool/secure/cluster/ca-chain-cert.pem",
        )
        output = []
        try:
            jobs = swm_api.get_jobs()
            if jobs:
                for job in jobs:
                    output.append(job.to_dict())
            else:
                output = "No jobs found"
        except httpx.ConnectError as e:
            output = f"Can't connect to swm-core ({url}): {e}"
        self.finish(json.dumps({"data": output}))


def setup_handlers(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]
    route_pattern = url_path_join(base_url, "swm-jupyter-term", "get_jobs")
    handlers = [(route_pattern, RouteHandler)]
    web_app.add_handlers(host_pattern, handlers)
