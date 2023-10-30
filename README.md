Sky Port Terminal for Jupyter
=============================

# Sky Port project

Sky Port is an universal bus between user software and compute resources. It can also be considered as a transportation layer between workload producers and compute resource providers. Sky Port makes it easy to connect user software to different cloud resources.

# Sky Port integration

The current project represents a custom spawner that allows to configure spawning options and submit jupyterlab job over Sky Port.
The spawner python package is distributed vis PyPI as `swm-jupyter-spawner`.

## Development environment for the spawner

Ensure `conda` and `pip` are installed and accessable via $PATH (installed in the dev container image by default).

### 1. Create conda environment
```bash
# Run the dev container from swm-core first, then switch to swm-jupyter-term directory
conda create -n swm-jupyter --override-channels --strict-channel-priority -c conda-forge -c anaconda nodejs configurable-http-proxy
conda init bash
```
Activate conda:
```bash
conda activate swm-jupyter
```

Deactivate conda:
```bash
conda deactivate
```

For local testing:
```bash
docker pull jupyter/datascience-notebook:hub-3.1.1
```

## 2. Configure virtualenv
```bash
make prepare-venv
```

# JupyterHub spawner

All you need to start using it is to have swm-core container running and then you start and login to jupyterhub.
In order to start jupyterhub manually in a terminal:
```bash
conda activate swm-jupyter
. .venv/bin/activate
jupyterhub
```

# Contributing

We appreciate all contributions. If you are planning to contribute back bug-fixes, please do so without any further discussion. If you plan to contribute new features, utility functions or extensions, please first open an issue and discuss the feature with us. 

# License

We use a shared copyright model that enables all contributors to maintain the copyright on their contributions.

This software is licensed under the [BSD-3-Clause license](LICENSE).
