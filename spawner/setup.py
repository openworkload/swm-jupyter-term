#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function

import os
import sys

from distutils.core import setup

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))

# Get the current package version
version_ns = {}
with open(pjoin(here, 'version.py')) as f:
    exec(f.read(), {}, version_ns)


def get_long_description():
    here = path.abspath(path.dirname(__file__))
    with open(path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
    return long_description


setup_args = dict(
    name='swm_jupyter_spawner',
    version=version_ns['__version__'],
    description="""A spawner for Jupyterhub to spawn notebooks over Sky Port""",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Taras Shapovalov",
    author_email="taras@iclouds.net",
    url="https://iclouds.net",
    license="BSD",
    platforms="Linux, Mac OS X, Windows",
    packages=setuptools.find_packages(),
    keywords=[
        "Interactive",
        "Interpreter",
        "Shell",
        "Web",
        "HPC",
        "High Performance Computing",
        "Cloud Computing",
        "SWM",
        "Sky Port",
        "Sky Workload Manager"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    project_urls={
        "Bug Reports": "https://github.com/skyworkflows/swm-jupyter-term/issues",
        "Source": "https://github.com/skyworkflows/swm-jupyter-term",
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
