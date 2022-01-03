import json
import platform

import httpx
import tornado
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
from notebook.notebookapp import NotebookApp
from swmclient.api import SwmApi


class RouteHandler(APIHandler):  # type: ignore
    @tornado.web.authenticated  # type: ignore
    def get(self) -> None:
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
                output = ["No jobs found"]
        except httpx.ConnectError as e:
            output = [f"Can't connect to swm-core ({url}): {e}"]
        self.finish(json.dumps({"data": output}))


def setup_handlers(web_app: NotebookApp) -> None:
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]
    route_pattern = url_path_join(base_url, "swm-jupyter-term", "get_jobs")
    handlers = [(route_pattern, RouteHandler)]
    web_app.add_handlers(host_pattern, handlers)
