import io
import time
import typing
import platform

from jupyterhub.spawner import Spawner
from swmclient.api import SwmApi
from swmclient.generated.models.job_state import JobState
from swmclient.generated.types import File
from traitlets import Integer, Unicode

from .form import SwmForm


class SwmSpawner(Spawner):  # type: ignore

    _jupyterhub_port = Integer(8081, help="JupyterHub port", config=True)
    _jupyterhub_host = Unicode("swm_server_host", help="JupyterHub hostname resolvable from container", config=True)
    _jupyter_singleuser_port = Integer(8888, help="jupyter server port", config=True)

    _swm_port = Integer(8443, help="swm-core user API port", config=True)
    _swm_host = Unicode(platform.node(), help="swm-core user API hostname", config=True)
    _swm_ca_file = Unicode("~/.swm/spool/secure/cluster/ca-chain-cert.pem", help="CA file path", config=True)
    _swm_key_file = Unicode("~/.swm/key.pem", help="PEM key file path", config=True)
    _swm_cert_file = Unicode("~/.swm/cert.pem", help="PEM certificate file path", config=True)
    _swm_job_id = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._html_form = SwmForm(self.log)
        self.options_form = self.render_options_form()

    @property
    def _swm_api(self) -> SwmApi:
        username = self.user.name
        return SwmApi(
            url=f"https://{self._swm_host}:{self._swm_port}",
            key_file=self._swm_key_file.format(username=username),
            cert_file=self._swm_cert_file.format(username=username),
            ca_file=self._swm_ca_file.format(username=username),
        )

    def load_state(self, state: typing.Dict[str, typing.Any]) -> None:
        """Restore state about swm-spawned server after a hub restart."""
        super().load_state(state)
        if "job_id" in state:
            self._swm_job_id = state["job_id"]
        if "remote_ip" in state:
            self.remote_ip = state["remote_ip"]
        if "remote_port" in state:
            self._jupyter_singleuser_port = state["remote_port"]

    def get_state(self) -> typing.Any:
        """Save state needed to restore this spawner instance after hub restore."""
        state = super().get_state()
        if self._swm_job_id:
            state["job_id"] = self._swm_job_id
        if self._jupyter_singleuser_ip:
            state["remote_ip"] = self._jupyter_singleuser_ip
        if self._jupyter_singleuser_port:
            state["remote_port"] = self._jupyter_singleuser_port
        return state

    def clear_state(self) -> None:
        """Clear stored state about this spawner."""
        super().clear_state()
        self._swm_job_id = ""
        self._jupyter_singleuser_ip = "127.0.0.1"
        self._jupyter_singleuser_port = 8888

    async def start(self) -> typing.Optional[tuple[str, int]]:
        """Start single-user server over SWM."""
        self._swm_job_id = await self._do_submit_rpc()
        self.log.debug(f"Starting User: {self.user.name}, job id: {self._swm_job_id}")

        if not self._swm_job_id:
            return None

        await self._wait_job_start()
        return self._jupyter_singleuser_ip, self._jupyter_singleuser_port

    async def poll(self) -> typing.Optional[int]:
        """Poll process to see if it is still running (None: not running, 0 otherwise)."""
        job_state = await self._fetch_job_state()
        if job_state in [JobState.R, JobState.W, JobState.T]:
            return None
        self.clear_state()
        return 0

    async def stop(self, now: bool = False) -> None:
        """Stop single-user server process for the current user."""
        await self._do_cancel_rpc()
        self.clear_state()

    async def _fetch_job_state(self) -> typing.Optional[JobState]:
        """Perform RPC call to SWM to fetch the job state"""
        if self._swm_job_id:
            job = self._swm_api.get_job(self._swm_job_id)
            if job:
                self.log.debug(f"Fetched job state: {job.state!s}")
                return job.state
            else:
                self.log.debug("Fetching job RPC did not return job")
        else:
            self.log.warning("Can't cancel job: ID is unknown")
        return None

    async def _do_submit_rpc(self) -> str:
        """Perform RPC to SWM in order to submit a new the singleuser job"""
        hub_url = f"http://{self._jupyterhub_host}:{self._jupyterhub_port}/hub/api"
        env = self.get_env()
        bash_script_str = "#!/bin/bash\n"
        bash_script_str += f"#SWM flavor {self.user_options['flavor']}\n"
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
        self.log.info(f"SWM job script: \n{bash_script_str}")

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

    async def _do_cancel_rpc(self) -> None:
        """Perform RPC to SWM in order to cancel the singleuser job"""
        if self._swm_job_id:
            output = self._swm_api.cancel_job(self._swm_job_id)
            for line in output.decode("utf-8").split("\n"):
                self.log.debug(f"Cancel RPC resulting line: {line.strip()}")
        else:
            self.log.warning("Can't cancel job: ID is unknown")

    async def _wait_job_start(self) -> None:
        if not self._swm_job_id:
            self.log.warning("Can't fetch job: ID is unknown")

        while True:
            if job := self._swm_api.get_job(self._swm_job_id):
                self.log.debug(f"Fetched job state: {job.state!s}")
                if job.state == JobState.R:
                    if job.node_ips:
                        self._jupyter_singleuser_ip = job.node_ips[0]
                        self.log.debug(f"Job {self._swm_job_id} main node IP: {self._jupyter_singleuser_ip}")
                    else:
                        self.log.warning(f"Job {self._swm_job_id} node IP list is empty")
                    break
                elif job.state == JobState.F:
                    self.log.warning(f"Job {self._swm_job_id} already finished")
                    break
                elif job.state == JobState.C:
                    self.log.warning(f"Job {self._swm_job_id} is canceled")
                    break
                elif job.state in [JobState.Q, JobState.W, JobState.T]:
                    self.log.debug(f"Job {self._swm_job_id} is not started yet, state={job.state!s}")
                time.sleep(10)
            else:
                self.log.warning("Fetching job RPC did not return anything")
                break

    def render_options_form(self) -> str:
        return self._html_form.render(self._swm_api)

    def options_from_form(self, form_data: typing.Dict[str, list[str]]) -> typing.Dict[str, typing.Any]:
        return self._html_form.get_options(form_data)
