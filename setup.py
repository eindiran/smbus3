# The MIT License (MIT)
# Copyright (c) 2017 Karl-Petter Lindegaard

import builtins
import os
import re

from setuptools import setup


def read_file(fname, encoding="utf-8"):
    with builtins.open(fname, encoding=encoding) as r:
        return r.read()


def find_version(*file_paths):
    fpath = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = read_file(fpath)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)

    err_msg = f"Unable to find version string in {fpath}"
    raise RuntimeError(err_msg)


README = read_file("README.md")
version = find_version("smbus3", "__init__.py")

setup(
    name="smbus3",
    version=version,
    author="Karl-Petter Lindegaard",
    author_email="kp.lindegaard@gmail.com",
    description="smbus3 is a drop-in replacement for smbus-cffi/smbus-python in pure Python",
    license="MIT",
    keywords=["smbus", "smbus3", "python", "i2c", "raspberrypi", "linux"],
    url="https://github.com/eindiran/smbus3",
    packages=["smbus3"],
    package_data={"smbus3": ["py.typed", "smbus3.pyi"]},
    long_description=README,
    long_description_content_type="text/markdown",
    extras_require={"docs": ["sphinx >= 1.5.3"], "qa": ["ruff"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
