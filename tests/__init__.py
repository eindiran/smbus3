"""
smbus3 - A drop-in replacement for smbus2/smbus-cffi/smbus-python

Tests for smbus: __init__.py is used to allow unittest to properly
collect the tests from the top directory.
"""

import unittest

import smbus3

from .test_datatypes import TestDataTypes
from .test_smbus3 import TestI2CMsg, TestI2CMsgRDWR, TestSMBus, TestSMBusWrapper

__version__ = "0.5.3"
__all__ = ["TestDataTypes", "TestI2CMsg", "TestI2CMsgRDWR", "TestSMBus", "TestSMBusWrapper"]


class TestSMBusVersion(unittest.TestCase):
    """
    Test that the version of the tests matches the version of smbus3.
    """

    def test_version(self):
        self.assertEqual(__version__, smbus3.__version__)
