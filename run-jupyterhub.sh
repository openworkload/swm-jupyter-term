#!/bin/bash

conda activate swm-jupyter
. .venv/bin/activate
jupyterhub --debug
