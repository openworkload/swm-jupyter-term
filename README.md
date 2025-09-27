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

* Start JupyterHub:
```bash
make start
```

## Run in release mode (in container)

* Build release container:
```bash
make build-container
```

* Start JupyterHub container:
```bash
make start-container
```

# Usage:
* Go to [http://localhost:8000](http://localhost:8000) in a web browser.
* Select notebook and other files that will be uploaded (if needed).
* Select flavor and image for VM machine (use filter if needed).
* Press "Start" button.

In 7-10 minutes JupyterLab will be started.


# Contributing

We appreciate all contributions. If you are planning to contribute back bug-fixes, please do so without any further discussion. If you plan to contribute new features, utility functions or extensions, please first open an issue and discuss the feature with us. 


# License

We use a shared copyright model that enables all contributors to maintain the copyright on their contributions.

This software is licensed under the [BSD-3-Clause license](LICENSE).
