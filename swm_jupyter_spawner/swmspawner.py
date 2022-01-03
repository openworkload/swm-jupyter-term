import io
import platform
import socket

from jupyterhub.spawner import Spawner
from swmclient.api import SwmApi
from swmclient.generated.models.job_state import JobState
from traitlets import Bool, Integer, Unicode, observe


class SwmSpawner(Spawner):

    _swm_port = Integer(8443, help="SWM port number", config=True)
    _swm_host = Unicode("localhost", help="SWM hostname", config=True)
    _swm_ca_file = Unicode("~/.swm/spool/secure/cluster/ca-chain-cert.pem", help="CA file path", config=True)
    _swm_key_file = Unicode("~/.swm/key.pem", help="PEM key file path", config=True)
    _swm_cert_file = Unicode("~/.swm/cert.pem", help="PEM certificate file path", config=True)
    _debug_singleuser_daemon = Bool(False, help="Enable debug messages for singleuser server", config=True)
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
        bash_script_str = "#!/bin/bash\n"
        bash_script_str += "#SWM relocatable\n"
        bash_script_str += "#SWM image jupyter/datascience-notebook\n"
        bash_script_str += "#SWM ports 8888/tcp\n"
        bash_script_str += "\n"
        bash_script_str += "cd /tmp\n"
        bash_script_str += "export JUPYTERHUB_API_TOKEN=swm\n"
        bash_script_str += f"export JUPYTERHUB_CLIENT_ID=oauth-{self.user.name}-$(hostname)\n"
        bash_script_str += "jupyterhub-singleuser --hub-api-url='http://swm_server_host:8081'"
        if self._debug_singleuser_daemon:
            bash_script_str += "--debug"
        bash_script_str += "\n"

        job_script_bytes = bytes(bash_script_str, "utf-8")
        io_bytes = io.BytesIO(job_script_bytes)
        io_obj: File = self._swm_api.submit_job(io_bytes)
        job_id: str = "UNDEFINED"
        while True:
            if line := io_obj.payload.readline():
                if not job_id:
                    job_id = line.decode("utf-8").strip()
                self.log.debug("Job sumbission RPC resulting line: {line}")
            else:
                self.log.debug("Job submission RPC did not produce any output")
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
            else:
                self.log.debug(f"Fetching job RPC did not return anything")


    @observe("remote_host")
    def _log_remote_host(self, change):
        self.log.debug(f"Remote host was set to {self.remote_host}")

    @observe("remote_ip")
    def _log_remote_ip(self, change):
        self.log.debug("Remote IP was set to {self.remote_ip}")