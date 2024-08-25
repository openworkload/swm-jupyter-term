#!/usr/bin/env python
# coding: utf-8

from codecs import open  # to use a consistent encoding
from os import path
from subprocess import check_output

from setuptools import setup, find_packages


def get_version():
    cmd = "git describe --tags"
    try:
        result = check_output(
            cmd.split(),
        ).decode('utf-8').strip().split("-")[0]
    except:
        result = "?"
    return result


def get_long_description():
    here = path.abspath(path.dirname(__file__))
    with open(path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
    return long_description


setup(
    name="swmjupyter",
    version=get_version(),
    description="A spawner for JupyterHub to spawn notebooks over Sky Port",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/openworkload/swm-jupyter-term",
    author="Taras Shapovalov",
    author_email="taras@iclouds.net",
    packages=find_packages(),
    license="BSD",
    include_package_data=True,
    python_requires=">=3.10, <4",
    platforms="Linux",
    keywords=[
        "HPC",
        "High Performance Computing",
        "Cloud Computing",
        "Open Workload",
        "Sky Port"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    project_urls={
        "Bug Reports": "https://github.com/openworkload/swm-jupyter-term/issues",
        "Source": "https://github.com/openworkload/swm-jupyter-term",
    },
)
