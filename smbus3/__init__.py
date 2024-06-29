"""
smbus3 - A drop-in replacement for smbus2/smbus-cffi/smbus-python
"""

from .smbus3 import I2C_M_Bitflag, I2cFunc, SMBus, i2c_msg

__version__ = "0.5.5"
__all__ = ["SMBus", "i2c_msg", "I2cFunc", "I2C_M_Bitflag", "__version__"]
