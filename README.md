<p align="center">
    <a href="https://github.com/openworkload/swm-jupyter-term/blob/master/LICENSE" alt="License">
        <img src="https://img.shields.io/github/license/openworkload/swm-jupyter-term" />
    </a>
    <a href="https://github.com/openworkload/swm-jupyter-term/actions/workflows/ci.yml" alt="Latest CI tests result">
        <img src="https://github.com/openworkload/swm-jupyter-term/actions/workflows/ci.yml/badge.svg?event=push" />
    </a>
</p>


Sky Port Juputer terminal
=============================

# Sky Port project

Sky Port makes it easy to consume cloud resources by user software. It can also be considered as a transportation layer between workload producers and compute resource providers.

# JupyterHub integration

The project in this repository represents a custom spawner that allows running jupyterlab server via Sky Port.
The spawner python package is distributed via PyPI: [swmjupyter](https://pypi.org/project/swmjupyter).

## Run in development mode

* Run skyport development container (`make cr` in swm-core directory) and go back to top sources directory of this repo.

* Install dependencies:
```bash
make prepare-venv
```

* Start JupyterHub (hub login must match your system username; that account
  needs `~/.swm/cert.pem` and `key.pem`):
```bash
export SWM_JUPYTER_ADMIN_USER=$USER
make start
```

The public UI binds to `127.0.0.1:8000` by default. See
[HOWTO/SECURITY.md](HOWTO/SECURITY.md) for OAuth, TLS, per-user mTLS, and
publish options.

## Run in release mode (in container)

* Build release container:
```bash
make build-container
```

* Start JupyterHub container:
```bash
make start-container
```

# Usage

Authentication is required. The default authenticator is NativeAuthenticator
(not open Dummy auth). See [HOWTO/SECURITY.md](HOWTO/SECURITY.md).

* Set `SWM_JUPYTER_ADMIN_USER` to your admin login, then start the hub.
* Open [http://127.0.0.1:8000](http://127.0.0.1:8000) (loopback by default).
* Sign in with your hub user.
* Select notebook and other files that will be uploaded (if needed).
* Select flavor and image for the VM (use filter if needed).
* Press **Start**.

In 7-10 minutes JupyterLab will be started.

For local demos only, you may set `SWM_JUPYTER_INSECURE_AUTH=1` with a
loopback bind. Do not use that on a network-facing host.

The release container runs as non-root `jupyterhub` and mounts that user's
Sky Port `cert.pem` / `key.pem` / CA **read-only**. Log in to the hub as
`jupyterhub` so the system-user mTLS mapping matches. Upload names are
sanitized into a dedicated spool. Details: [HOWTO/SECURITY.md](HOWTO/SECURITY.md).


# Contributing

We appreciate all contributions. If you are planning to contribute back bug-fixes, please do so without any further discussion. If you plan to contribute new features, utility functions or extensions, please first open an issue and discuss the feature with us. 


# License

We use a shared copyright model that enables all contributors to maintain the copyright on their contributions.

This software is licensed under the [BSD-3-Clause license](LICENSE).
