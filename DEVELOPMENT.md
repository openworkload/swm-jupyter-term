Sky Port Juputer terminal development
=====================================

Ensure `conda` and `pip` are installed and accessable via $PATH (installed in the dev container image by default).

### 1. Create conda environment
```bash
# Run the dev container from skyport-dev first, then switch to swm-jupyter-term directory
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

Pull contaienr image for local testing:
```bash
docker pull jupyter/datascience-notebook:hub-3.1.1
```

## 2. Configure virtualenv
```bash
make prepare-venv
```

# JupyterHub spawner

In `skyport-dev` container start `jupyterhub`:
```bash
conda activate swm-jupyter
. .venv/bin/activate
jupyterhub
```
