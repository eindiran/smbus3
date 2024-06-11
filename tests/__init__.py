"""
smbus3 - A drop-in replacement for smbus2/smbus-cffi/smbus-python

Tests for smbus: __init__.py is used to allow unittest to properly
collect the tests from the top directory.
"""

from .test_datatypes import TestDataTypes
from .test_smbus3 import TestI2CMsg, TestI2CMsgRDWR, TestSMBus, TestSMBusWrapper

__version__ = "0.5.0"
__all__ = ["TestDataTypes", "TestI2CMsg", "TestI2CMsgRDWR", "TestSMBus", "TestSMBusWrapper"]
