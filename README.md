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

# Overview

Sky Port is an universal bus between user software and compute resources.
It can also be considered as a transportation layer between workload producers and compute resource providers.
Sky Port makes it easy to connect user software to different cloud resources.

# JupyterHub integration

The project in this repository represents a custom spawner that allows spawning jupyterlab server over Sky Port.
The spawner python package is distributed via PyPI: [swmjupyter](https://pypi.org/project/swmjupyter).

## How to run in development mode

1. Run skyport dev container and go to top sources directory of this repo.

2. Install dependencies:
```bash
make prepare-venv
```

3. Start JupyterHub:
```bash
make run
```

4. Submit Sky Port job:
    a. go to `http://localhost:8000` in a web browser,
    b. select notebook and other files that will be uploaded (if needed),
    c. select flavor for VM machine (or use name filter if needed),
    d. click "Start" button.

In 10-15 minutes JupyterLab will be started in Azure.


# Contributing

We appreciate all contributions. If you are planning to contribute back bug-fixes, please do so without any further discussion. If you plan to contribute new features, utility functions or extensions, please first open an issue and discuss the feature with us. 


# License

We use a shared copyright model that enables all contributors to maintain the copyright on their contributions.

This software is licensed under the [BSD-3-Clause license](LICENSE).
