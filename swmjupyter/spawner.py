import io
import os
import typing
from datetime import datetime
from queue import Queue
from tempfile import TemporaryDirectory

from jinja2 import Template
from jupyterhub.spawner import Spawner
from swmclient.api import SwmApi
from swmclient.generated.models.job_state import JobState
from tornado import gen
from traitlets import Integer, Unicode

from .form import SwmForm

# Staged into the job directory via #SWM input-files (must match upload_paths rules).
HUB_API_TOKEN_FILENAME = "jupyterhub_api_token"


def write_hub_api_token_file(spool_dir: str, token: str) -> str:
    """Write the Hub API token to a mode-0600 file under the upload spool."""
    path = os.path.join(spool_dir, HUB_API_TOKEN_FILENAME)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, token.encode("utf-8"))
    finally:
        os.close(fd)
    os.chmod(path, 0o600)
    return path


def summarize_job_script_for_log(script: str, token: str) -> str:
    """Return a log line for the job script without exposing the Hub API token."""
    body = script.replace(token, "***") if token else script
    return f"Job script to submit ({len(script)} bytes):\n{body}"


class SwmSpawner(Spawner):  # type: ignore

    _config_file = Unicode(os.path.expanduser("~/.swm/jupyter-spawner.conf"), help="Gate config file", config=True)

    _jupyterhub_port = Integer(8081, help="JupyterHub port", config=True)
    _jupyterhub_host = Unicode("localhost", help="JupyterHub hostname resolvable from container", config=True)
    _jupyter_singleuser_port = Integer(8888, help="jupyter server port", config=True)

    _swm_port = Integer(8443, help="swm-core user API port", config=True)
    _swm_host = Unicode(
        os.getenv("SKYPORT_HOST", "skyport.openworkload.org"), help="swm-core user API host", config=True
    )
    _swm_ca_file = Unicode("~/.swm/spool/secure/cluster/ca-chain-cert.pem", help="CA file path", config=True)
    _swm_key_file = Unicode("~/.swm/key.pem", help="PEM key file path", config=True)
    _swm_cert_file = Unicode("~/.swm/cert.pem", help="PEM certificate file path", config=True)
    _upload_root = Unicode(
        os.environ.get("SWM_JUPYTER_UPLOAD_ROOT", ""),
        help="Parent directory for per-spawner upload spools",
        config=True,
    )
    _swm_job_id = None

    _msg_queue: Queue[tuple[str, int]] = Queue()
    _last_msg: str = ""

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        upload_parent = self._upload_root.strip() or None
        if upload_parent:
            os.makedirs(upload_parent, mode=0o700, exist_ok=True)
        # One spool per spawner instance (never a shared class attribute).
        self._spool_dir = TemporaryDirectory(prefix=".swmjupyter_", dir=upload_parent)
        self._config = self._read_config()
        self._html_form = SwmForm(self.log)
        self.options_form = self.render_options_form()

    def _read_config(self) -> dict[str, str]:
        config: dict[str, str] = {}
        with open(self._config_file, "r") as file:
            for line in file:
                if not line:
                    continue
                stripped_line = line.strip()
                if stripped_line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                parts = stripped_line.split("=", 1)
                if len(parts) != 2:
                    continue
                config[parts[0].strip().lower()] = parts[1].strip()
        self.log.info(f"Configuration from {self._config_file}: {config}")
        return config

    def _render_job_script(self) -> str:
        env = self.get_env()
        api_token = env["JUPYTERHUB_API_TOKEN"]
        token_path = write_hub_api_token_file(self._spool_dir.name, api_token)
        input_files = list(self.user_options.get("input_files") or [])
        input_files.append(token_path)

        jupyterhub_port = self._config.get("jupyterhub_port", self._jupyterhub_port)
        jupyterhub_host = self._config.get("jupyterhub_host", self._jupyterhub_host)
        jupyter_singleuser_port = self._config.get("jupyter_singleuser_port", self._jupyter_singleuser_port)
        job_info: dict[str, str | int | list[str]] = {
            "account": self._config.get("account", "openstack"),
            "container_registry": self._config.get("container_registry", "swmregistry.azurecr.io"),
            "container_image_name": self._config.get("container_image_name", "jupyter/pytorch-notebook"),
            "server_port": jupyter_singleuser_port,
            "container_image_tag": self._config.get("container_image_tag", "cuda12-hub-5.2.1"),
            "cloud_image_name": self.user_options["cloud-image"],
            "flavor": self.user_options["flavor"],
            "gpus": self.user_options["gpus"],
            "ports": f"{jupyter_singleuser_port}/tcp/in,{jupyterhub_port}/tcp/out",
            "jupyterhub_client_id": env["JUPYTERHUB_CLIENT_ID"],
            "hub_url": f"http://{jupyterhub_host}:{jupyterhub_port}/hub/api",
            "input_files": input_files,
            "output_files": self.user_options.get("output_files") or [],
            "storage": self._config.get("storage", "swmblobcontainer"),
        }
        with open(os.path.dirname(__file__) + "/job.sh.jinja") as _file:
            job_script = Template(_file.read())
        job_script_rendered = str(job_script.render(job_info=job_info))
        self.log.info(summarize_job_script_for_log(job_script_rendered, api_token))
        if api_token and api_token in job_script_rendered:
            self.log.error("Hub API token unexpectedly present in rendered job script")
            raise RuntimeError("Hub API token must not appear in the job script")
        return job_script_rendered

    @property
    def _swm_api(self) -> SwmApi:
        username = self.user.name
        key_file = os.path.expanduser(self._swm_key_file.format(username=username))
        cert_file = os.path.expanduser(self._swm_cert_file.format(username=username))
        ca_file = os.path.expanduser(self._swm_ca_file.format(username=username))
        swm_core_addr = f"https://{self._swm_host}:{self._swm_port}"
        self.log.info(f"Sky Port core address: {swm_core_addr}")
        return SwmApi(
            url=swm_core_addr,
            key_file=key_file,
            cert_file=cert_file,
            ca_file=ca_file,
        )

    def load_state(self, state: dict[str, typing.Any]) -> None:
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

    async def start(self) -> tuple[str, int] | None:
        """Start single-user server over SWM."""
        self._swm_job_id = await self._do_submit_rpc()
        self._add_msg(f"Job submitted: {self._swm_job_id}", 1)
        self.log.debug(f"Starting User: {self.user.name}, job id: {self._swm_job_id}")

        if not self._swm_job_id:
            return None

        await self._wait_job_start()
        self.log.info("Job start waiting finished")
        return self._jupyter_singleuser_ip, self._jupyter_singleuser_port

    async def poll(self) -> int | None:
        """Poll process to see if it is still running (None: not running, 0 otherwise)."""
        job_state = await self._fetch_job_state()
        if job_state in [JobState.R, JobState.W, JobState.T]:
            return None
        if job_state == JobState.E:
            await self.stop()
            return None
        self.clear_state()
        return 0

    async def stop(self, now: bool = False) -> None:
        """Stop single-user server process for the current user."""
        await self._do_cancel_rpc()
        self.clear_state()

    async def _fetch_job_state(self) -> typing.Any:
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

    async def progress(self) -> typing.AsyncGenerator[int, None] | None:
        while True:
            if not self._msg_queue.empty():
                msg, progress = self._msg_queue.get()
                if self._last_msg != msg:
                    self._last_msg = msg
                    current_time = datetime.now().strftime("%H:%M:%S")
                    yield {"progress": progress, "message": f"{current_time}: {msg}"}
                self._msg_queue.task_done()
            else:
                await gen.sleep(2)
            if self.ready:
                self.log.debug("Server is ready => exit start progress tracking")
                break

    async def _do_submit_rpc(self) -> str:
        """Perform RPC to SWM in order to submit a new singleuser job"""
        job_script = self._render_job_script()
        job_id: str = ""
        job_script_bytes = bytes(job_script, "utf-8")
        io_bytes = io.BytesIO(job_script_bytes)
        if io_obj := self._swm_api.submit_job(io_bytes):
            while True:
                if line := io_obj.payload.readline():
                    if not job_id:
                        job_id = line.decode("utf-8").strip()
                    self.log.debug(f"Job sumbission RPC resulting line: {line}")
                else:
                    break
        else:
            self.log.error("Can't submit a job: no job ID is returned")
        return job_id

    async def _do_cancel_rpc(self) -> None:
        """Perform RPC to SWM in order to cancel the singleuser job"""
        if self._swm_job_id:
            output = self._swm_api.cancel_job(self._swm_job_id)
            for line in output.decode("utf-8").split("\n"):
                self.log.debug(f"Cancel RPC resulting line: {line.strip()}")
        else:
            self.log.warning("Can't cancel job: ID is unknown")

    def _add_msg(self, msg: str, progress: int) -> None:
        self._msg_queue.put((msg, progress))

    async def _wait_job_start(self) -> None:
        while True:
            if job := self._swm_api.get_job(self._swm_job_id):
                self.log.debug(f"Fetched job state: {job.state!s}")
                if job.state == JobState.R:
                    if job.node_ips:
                        self._jupyter_singleuser_ip = job.node_ips[0]
                        msg = f"Job is running (IP: {self._jupyter_singleuser_ip}): {job.state_details}"
                        self.log.debug(msg)
                        self._add_msg(msg, 99)
                    else:
                        msg = f"Job {self._swm_job_id} node IP list is empty: {job.state_details}"
                        self._add_msg(msg, 99)
                        self.log.warning(msg)
                    self.log.debug("Exit job waiting loop")
                    break
                elif job.state == JobState.F:
                    msg = f"Job is finished: {job.state_details}"
                    self._add_msg(msg, 100)
                    self.log.warning(msg)
                    break
                elif job.state == JobState.C:
                    msg = f"Job is canceled: {job.state_details}"
                    self._add_msg(msg, 100)
                    self.log.warning(msg)
                    break
                elif job.state == JobState.E:
                    msg = f"Job failed: {job.state_details}"
                    self._add_msg(msg, 100)
                    self.log.warning(msg)
                    break
                elif job.state == JobState.Q:
                    msg = f"Job is pending: {job.state_details}"
                    if job.state_details.lower().startswith("data uploaded"):
                        progress = 90
                    else:
                        progress = 5
                elif job.state == JobState.W:
                    msg = f"Job is waiting to start: {job.state_details}"
                    if job.state_details.lower().startswith("initiate a new partition"):
                        progress = 10
                    elif job.state_details.lower().startswith("partition spawned"):
                        progress = 15
                    elif job.state_details.lower().startswith("partition has not been created yet"):
                        progress = 17
                    elif job.state_details.lower().startswith("waiting for ssh provisioning port"):
                        progress = 20
                    elif job.state_details.lower().startswith("uploading the worker"):
                        progress = 25
                    elif job.state_details.lower().startswith("start secured tunnel"):
                        progress = 50
                    elif job.state_details.lower().startswith(
                        "sky port connected"
                    ) or job.state_details.lower().startswith("waiting for sky port port readiness"):
                        progress = 70
                    elif job.state_details.lower().startswith("data uploaded"):
                        progress = 95
                elif job.state == JobState.T:
                    progress = 80
                    msg = f"Job data is transferring: {job.state_details}"

                self._add_msg(msg, progress)
                self.log.debug(msg)
                await gen.sleep(10)
            else:
                msg = "Fetching job RPC returned nothing!"
                self._add_msg(msg, 99)
                self.log.warning(msg)
                break

    def render_options_form(self) -> str:
        return self._html_form.render(self._swm_api)

    def options_from_form(self, form_data: dict[str, list[dict[str, bytes]]]) -> dict[str, typing.Any]:
        return self._html_form.get_options(form_data, self._spool_dir.name)
