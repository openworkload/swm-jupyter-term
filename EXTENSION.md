# swm_jupyter_ext

[![Github Actions Status](https://github.com/skyworkflows/swm-jupyter-term/workflows/Build/badge.svg)](https://github.com/skyworkflows/swm-jupyter-term/actions/workflows/build.yml)[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/skyworkflows/swm-jupyter-term/main?urlpath=lab)

A JupyterLab extension for Sky Port Terminal.


This extension is composed of a Python package named `swm_jupyter_ext`
for the server extension and a NPM package named `swm-jupyter-ext`
for the frontend extension.

## Development environment

### Create
conda create -n jupyterlab-ext --override-channels --strict-channel-priority -c conda-forge -c anaconda jupyterhub jupyterlab=3 cookiecutter nodejs jupyter-packaging git
conda init bash

## Activate
conda activate jupyterlab-ext

## Deactivate
conda deactivate


## Requirements

* JupyterLab >= 3.0

## Install

To install the extension, execute:

```bash
pip install swmclient swm_jupyter_ext
```

## Uninstall

To remove the extension, execute:

```bash
pip uninstall swmclient swm_jupyter_ext
```


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


## Contributing

### Development install

Note: You will need NodeJS to build the extension package.

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Change directory to the swm_jupyter_ext directory
# Install package in development mode
pip install -e .
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
pip uninstall swm_jupyter_ext
```

In development mode, you will also need to remove the symlink created by `jupyter labextension develop`
command. To find its location, you can run `jupyter labextension list` to figure out where the `labextensions`
folder is located. Then you can remove the symlink named `swm-jupyter-ext` within that folder.


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