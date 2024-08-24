#!/usr/bin/env python3

import os
import sys

from distutils.core import setup
from pathlib import Path
from setuptools import find_packages

HERE = Path(__file__).parent.resolve()

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
    with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
    return long_description


setup_args = dict(
    name='swm_jupyter_spawner',
    version=get_version(),
    description="""A spawner for Jupyterhub to spawn notebooks over Sky Port""",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Taras Shapovalov",
    author_email="taras@iclouds.net",
    url="https://github.com/openworkload/swm-jupyter-term",
    license="BSD",
    platforms="Linux, Mac OS X, Windows",
    packages=find_packages(),
    keywords=[
        "HPC",
        "High Performance Computing",
        "Cloud Computing",
        "Sky Port",
        "Open Workload"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
        "Framework :: Jupyter",
        "Framework :: Jupyter :: JupyterLab",
        "Framework :: Jupyter :: JupyterLab :: 3",
        "Framework :: Jupyter :: JupyterLab :: Extensions",
        "Framework :: Jupyter :: JupyterLab :: Extensions :: Prebuilt",
    ],
    project_urls={
        "Bug Reports": "https://github.com/openworkload/swm-jupyter-term/issues",
        "Source": "https://github.com/openworkload/swm-jupyter-term",
    },
)

# setuptools requirements
if "setuptools" in sys.modules:
    setup_args["install_requires"] = install_requires = []
    with open("requirements.txt") as f:
        for line in f.readlines():
            req = line.strip()
            if not req or req.startswith(("-e", "#")):
                continue
            install_requires.append(req)


def main():
    setup(**setup_args)

if __name__ == "__main__":
    main()
