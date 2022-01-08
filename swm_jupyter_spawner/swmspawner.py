import io
import platform
import socket
import time

from jinja2 import BaseLoader
from jinja2 import Environment
from jupyterhub.spawner import Spawner
from swmclient.api import SwmApi
from swmclient.generated.models.job_state import JobState
from traitlets import Bool, Integer, Unicode, observe


class SwmSpawner(Spawner):

    _jupyterhub_port = Integer(8081, help="JupyterHub port", config=True)
    _jupyterhub_host = Unicode("swm_server_host", help="JupyterHub hostname resolvable from container", config=True)

    _swm_port = Integer(8443, help="swm-core user API port", config=True)
    _swm_host = Unicode("localhost", help="swm-core user API hostname", config=True)
    _swm_ca_file = Unicode("~/.swm/spool/secure/cluster/ca-chain-cert.pem", help="CA file path", config=True)
    _swm_key_file = Unicode("~/.swm/key.pem", help="PEM key file path", config=True)
    _swm_cert_file = Unicode("~/.swm/cert.pem", help="PEM certificate file path", config=True)
    _job_id = None

    @property
    def _swm_api(self) -> SwmApi:
        username = self.user.name
        return SwmApi(
            url=f"https://{self._swm_host}:{self._swm_port}",
            key_file=self._swm_key_file.format(username=username),
            cert_file=self._swm_cert_file.format(username=username),
            ca_file=self._swm_ca_file.format(username=username),
        )

    def load_state(self, state):
        """Restore state about swm-spawned server after a hub restart."""
        super().load_state(state)
        if "job_id" in state:
            self._job_id = state["job_id"]
        if "remote_ip" in state:
            self.remote_ip = state["remote_ip"]
        if "remote_port" in state:
            self._remote_port = state["remote_port"]

    def get_state(self):
        """Save state needed to restore this spawner instance after hub restore."""
        state = super().get_state()
        if self._job_id:
            state["job_id"] = self._job_id
        if self._remote_ip:
            state["remote_ip"] = self._remote_ip
        if self._remote_port:
            state["remote_port"] = self._remote_port
        return state

    def clear_state(self):
        """Clear stored state about this spawner."""
        super().clear_state()
        self._job_id = ""
        self._remote_ip = "127.0.0.1"
        self._remote_port = 8888

    async def start(self):
        """Start single-user server over SWM."""
        self._job_id = await self._do_submit_rpc()
        self.log.debug(f"Starting User: {self.user.name}, job id: {self._job_id}")

        if not self._job_id:
            return None

        await self._wait_job_start()
        return self._remote_ip, self._remote_port

    async def poll(self):
        """Poll process to see if it is still running (None: not running, 0 otherwise)."""
        job_state = await self._fetch_job_state()
        if job_state in [JobState.R, JobState.W, JobState.T]:
            return None
        self.clear_state()
        return 0

    async def stop(self, now=False):
        """Stop single-user server process for the current user."""
        alive = await self._do_cancel_rpc()
        self.clear_state()

    async def _fetch_job_state(self):
        """Perform RPC call to SWM to fetch the job state"""
        if self._job_id:
            job = self._swm_api.get_job(self._job_id)
            if job:
                self.log.debug(f"Fetched job state: {job.state!s}")
                return job.state
            else:
                self.log.debug(f"Fetching job RPC did not return job")
        else:
            self.log.debug("Can't cancel job: ID is unknown")

    async def _do_submit_rpc(self) -> str:
        """Perform RPC to SWM in order to submit a new the singleuser job"""
        hub_url = f"http://{self._jupyterhub_host}:{self._jupyterhub_port}/hub/api"
        env = self.get_env()
        bash_script_str = "#!/bin/bash\n"
        bash_script_str += "#SWM relocatable\n"
        bash_script_str += "#SWM image jupyter/datascience-notebook\n"
        bash_script_str += "#SWM ports 8888/tcp\n"
        bash_script_str += "\n"
        bash_script_str += "export HOME=/home/$USER\n"
        bash_script_str += "export XDG_CACHE_HOME=/home/$USER/.cache/\n"
        bash_script_str += "cd $HOME\n"
        bash_script_str += f"export JUPYTERHUB_API_TOKEN={env['JUPYTERHUB_API_TOKEN']}\n"
        bash_script_str += f"export JUPYTERHUB_CLIENT_ID={env['JUPYTERHUB_CLIENT_ID']}\n"
        bash_script_str += "export JUPYTER_RUNTIME_DIR=/tmp\n"
        bash_script_str += "export JUPYTERHUB_USER=$USER\n"
        bash_script_str += "export JUPYTERHUB_SERVICE_PREFIX=/user/$USER\n"
        bash_script_str += "env\n"
        bash_script_str += f"jupyterhub-singleuser --debug --ip='0.0.0.0' --hub-api-url='{hub_url}'\n"

        job_script_bytes = bytes(bash_script_str, "utf-8")
        io_bytes = io.BytesIO(job_script_bytes)
        io_obj: File = self._swm_api.submit_job(io_bytes)
        job_id: str = ""
        while True:
            if line := io_obj.payload.readline():
                if not job_id:
                    job_id = line.decode("utf-8").strip()
                self.log.debug(f"Job sumbission RPC resulting line: {line}")
            else:
                break
        return job_id

    async def _do_cancel_rpc(self):
        """Perform RPC to SWM in order to cancel the singleuser job"""
        if self._job_id:
            output = self._swm_api.cancel_job(self._job_id)
            for line in output.decode("utf-8").split("\n"):
                self.log.debug(f"Cancel RPC resulting line: {line.strip()}")
        else:
            self.log.debug("Can't cancel job: ID is unknown")


    async def _wait_job_start(self) -> None:
        if not self._job_id:
            self.log.debug("Can't fetch job: ID is unknown")

        while True:
            if job := self._swm_api.get_job(self._job_id):
                self.log.debug(f"Fetched job state: {job.state!s}")
                if job.state == JobState.R:
                    if job.node_ips:
                        self._remote_ip = job.node_ips[0]
                        self.log.debug(f"Job {self._job_id} main node IP: {self._remote_ip}")
                    else:
                        self.log.debug(f"Job {self._job_id} node IP list is empty")
                    break
                elif job.state == JobState.F:
                    self.log.debug(f"Job {self._job_id} already finished")
                    break
                elif job.state == JobState.C:
                    self.log.debug(f"Job {self._job_id} is canceled")
                    break
                elif job.state in [JobState.Q, JobState.W, JobState.T]:
                    self.log.debug(f"Job {self._job_id} is not started yet, state={job.state!s}")
                time.sleep(10)
            else:
                self.log.debug(f"Fetching job RPC did not return anything")
                break


    @observe("remote_host")
    def _log_remote_host(self, change):
        self.log.debug(f"Remote host was set to {self.remote_host}")

    @observe("remote_ip")
    def _log_remote_ip(self, change):
        self.log.debug("Remote IP was set to {self.remote_ip}")

    _remote_sites_form = Unicode(
        """
        <style>
        #swm-remote-sites-list label p {
            font-weight: normal;
        }
        </style>
        <div class='form-group' id='swm-remote-sites-list'>
        {% for remote_site in remote_site_list %}
        <label for='remote-site-item-{{ remote_site.name }}' class='form-control input-group'>
            <div class='col-md-1'>
                <input type='radio' name='remote_site' id='remote-site-item-{{ remote_site.name }}' value='{{ remote_site.name }}'/>
            </div>
            <div class='col-md-11'>
                <strong>{{ remote_site.server }}</strong>
                <p>{{ remote_site.kind }}</p>
            </div>
        </label>
        {% endfor %}
        </div>
        """,
        config=True,
        help="""
        Jinja2 template for constructing remote sites list shown to user.
        Used when `remote_site_list` is set.
        The contents of `remote_site_list` are passed in to the template.
        This should be used to construct the contents of a HTML form. When
        posted, this form is expected to have an item with name `remote_site` and
        the value the index of the remote_site in `remote_site_list`.
        """,
    )

    def render_options_form(self):
        remote_sites_form = Environment(loader=BaseLoader).from_string(self._remote_sites_form)
        remote_sites = self._swm_api.get_remote_sites()
        return remote_sites_form.render(remote_site_list=remote_sites)
