import json
import typing
from pathlib import Path

from jupyterlab.labapp import LabApp

from .handlers import setup_handlers

HERE = Path(__file__).parent.resolve()
with (HERE / "labextension" / "package.json").open() as fid:
    data = json.load(fid)


def _jupyter_labextension_paths() -> list[typing.Dict[str, str]]:
    return [{"src": "labextension", "dest": data["name"]}]


def _jupyter_server_extension_points() -> list[typing.Dict[str, str]]:
    return [{"module": "swm_jupyter_ext"}]


def _load_jupyter_server_extension(server_app: LabApp) -> None:
    """Registers the API handler to receive HTTP requests from the frontend extension.

    Parameters
    ----------
    server_app: jupyterlab.labapp.LabApp
        JupyterLab application instance
    """
    setup_handlers(server_app.web_app)
    server_app.log.info("Registered extension at URL path /swm-jupyter-ext")


# For backward compatibility with notebook server - useful for Binder/JupyterHub
load_jupyter_server_extension = _load_jupyter_server_extension
