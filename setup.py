#!/usr/bin/env python3
#Filename: setup.py
# coding: utf-8

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

import io
import os

from setuptools import find_packages
from setuptools import setup

NAME = "w3rkstatt"
VERSION = "20.21.05.00"
DESCRIPTION_FILE ="SETUP.md"


def read(filename):
    filename = os.path.join(os.path.dirname(__file__), filename)
    text_type = type(u"")
    with io.open(filename, mode="r", encoding='utf-8') as fd:
        return fd.read()



setup(
    name=NAME,
    version=VERSION,
    author="Orchestrator",
    author_email="orchestrator@bmc.com",
    url="https://github.com/Orch3strator/w3rkstatt",
    license='GNU',

    description="Orchestrator's Integration Platform for commercial and open source projects.",
    long_description=read(DESCRIPTION_FILE),
    long_description_content_type="text/markdown",

    keywords=['bmc', 'w3rkstatt'],
    project_urls={
        "Bug Tracker": "https://github.com/Orch3strator/w3rkstatt/issues",
    },

    include_package_data=True,
    install_requires=(
        'wheel','python_dateutil','six','pytz','numpy','pandas','urllib3','chardet','certifi','idna','requests','pyCryptodome','json2html','jsonpath-ng','jsonpath_rw_ext'
    ),

    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Unix",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Logging",
        "Topic :: Utilities",
    ],
    package_dir={"": "src"},
    packages=find_packages(exclude=('tests',),where='./src'),
    python_requires=">=3.6",
    platforms='Posix; MacOS X; Windows',
)
