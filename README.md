[!(https://github.com/skyworkflows/swm-jupyter-term/workflows/Build/badge.svg)](https://github.com/skyworkflows/swm-jupyter-term/actions/workflows/build.yml)[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/skyworkflows/swm-jupyter-term/main?urlpath=lab)

Sky Port Terminal for JupyterLab
===============================

# Sky Port project

Sky Port is an universal bus between user software and compute resources. It can also be considered as a transportation layer between workload producers and compute resource providers. Sky Port makes it easy to connect user software to different cloud resources.

# Sky Port JupyterLab integration

The current project consists of two components:

* **[JupyterLab extension](#jupyterlab-extension)**
* **[JupyterHub spawner](#jupyterhab-spawner)**

The both are python packages that (for a user convinience) are united into a single package `swmjupyter`.


# JupyterLab extension

This extension is composed of a Python package named `swm_jupyter_ext` for the server extension and a NPM package named `swm-jupyter-ext` for the frontend extension. The both are part of the main `swmjupyter` package.

## Development environment for the extension

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

## Requirements

* JupyterLab >= 3.0

## Troubleshoot

If you are seeing the frontend extension, but it is not working, check
that the server extension is enabled:

```bash
jupyter server extension list
```

If the server extension is installed and enabled, but you are not seeing
the frontend extension, check the frontend extension is installed:

```bash
jupyter labextension list
```

### Development install

Note: You will need NodeJS to build the extension package.

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Activate environment
conda activate swm-jupyter
make prepare-venv
. .venv/bin/activate
# Link your development version of the extension with JupyterLab
jupyter labextension develop . --overwrite
# Server extension must be manually installed in develop mode
jupyter server extension enable swm_jupyter_ext
# Rebuild extension Typescript source after making changes
jlpm run build
```

You can watch the source directory and run JupyterLab at the same time in different terminals to watch for changes in the extension's source and automatically rebuild the extension.

```bash
# Watch the source directory in one terminal, automatically rebuilding when needed
jlpm run watch
# Run JupyterLab in another terminal
jupyter lab
```

With the watch command running, every saved change will immediately be built locally and available in your running JupyterLab. Refresh JupyterLab to load the change in your browser (you may need to wait several seconds for the extension to be rebuilt).

By default, the `jlpm run build` command generates the source maps for this extension to make it easier to debug using the browser dev tools. To also generate source maps for the JupyterLab core extensions, you can run the following command:

```bash
jupyter lab build --minimize=False
```

### Development uninstall

```bash
# Server extension must be manually disabled in develop mode
jupyter server extension disable swm_jupyter_ext
pip uninstall swmjupyter
```

In development mode, you will also need to remove the symlink created by `jupyter labextension develop` command. To find its location, you can run `jupyter labextension list` to figure out where the `labextensions` folder is located. Then you can remove the symlink named `swm-jupyter-ext` within that folder.


### Before commit

Make sure that eslint passes:

```bash
jlpm run eslint:check
```

If there are any issues it might be possible to autofix them with:

```bash
jlpm run eslint
```

Run tests:

```bash
python -m pytest
```

### Packaging the extension

See [RELEASE](RELEASE.md)

### Additional links

* https://jupyter-server.readthedocs.io/en/latest/developers/extensions.html
* https://github.com/jupyterlab/extension-examples/tree/master/server-extension
* https://github.com/jupyterlab-contrib/spellchecker


# JupyterHub spawner


# Contributing

We appreciate all contributions. If you are planning to contribute back bug-fixes, please do so without any further discussion. If you plan to contribute new features, utility functions or extensions, please first open an issue and discuss the feature with us. 

# License

We use a shared copyright model that enables all contributors to maintain the copyright on their contributions.

This software is licensed under the BSD-3-Clause license.
