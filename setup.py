import builtins
import os
import re

from setuptools import setup  # type: ignore


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


README = read_file("README.rst")
version = find_version("smbus3", "__init__.py")
description = (
    "smbus3 is a drop-in replacement for smbus2, smbus-cffi, smbus-python "
    + "written in pure Python, intended for use with Python 3.9+"
)

setup(
    name="smbus3",
    version=version,
    author="Elliott Indiran",
    author_email="elliott.indiran@protonmail.com",
    description=description,
    license="MIT",
    keywords=["smbus", "smbus2", "smbus3", "python", "i2c", "raspberrypi", "linux"],
    url="https://github.com/eindiran/smbus3",
    packages=["smbus3"],
    package_data={"smbus3": ["py.typed", "smbus3.pyi"]},
    long_description=README,
    long_description_content_type="text/x-rst",
    extras_require={
        "docs": ["sphinx >= 7.0.0"],
        "qa": ["ruff >= 0.4.8", "mypy >= 1.10.0", "coverage >= 7.5.3"],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
