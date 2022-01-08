Sky Port Terminal for Jupyter
=============================

# Sky Port project

Sky Port is an universal bus between user software and compute resources. It can also be considered as a transportation layer between workload producers and compute resource providers. Sky Port makes it easy to connect user software to different cloud resources.

# Sky Port integration

The current project represents a custom spawner that allows to configure spawning options and submit jupyterlab job over Sky Port.
The spawner python package is distributed vis PyPI as `swmjupyter`.

## Development environment for the spawner

Ensure `conda` is installed and accessable via $PATH.

### Create
```bash
conda create -n swm-jupyter --override-channels --strict-channel-priority -c conda-forge -c anaconda nodejs configurable-http-proxy
conda init bash
```

## Activate
```bash
conda activate swm-jupyter
```

## Deactivate
```bash
conda deactivate
```

# JupyterHub spawner

All you need to start using it is to have swm-core container running and then you start and login to jupyterhub.
In order to start jupyterhub manually in a terminal:
```bash
conda activate swm-jupyter
. .venv/bin/activate
jupyterhub
```

https://github.com/jupyterhub/kubespawner/blob/d59c14cc3bcf4fead2d339ba6f7b549262f2deff/kubespawner/spawner.py#L2745

# Contributing

We appreciate all contributions. If you are planning to contribute back bug-fixes, please do so without any further discussion. If you plan to contribute new features, utility functions or extensions, please first open an issue and discuss the feature with us. 

# License

We use a shared copyright model that enables all contributors to maintain the copyright on their contributions.

This software is licensed under the [BSD-3-Clause license](LICENSE).
