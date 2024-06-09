"""
smbus3 - A drop-in replacement for smbus2/smbus-cffi/smbus-python
"""

import os
from ctypes import (
    POINTER,
    Structure,
    Union,
    c_char,
    c_uint8,
    c_uint16,
    c_uint32,
    create_string_buffer,
    string_at,
)
from enum import IntFlag
from fcntl import ioctl

# Commands from uapi/linux/i2c-dev.h
I2C_RETRIES = 0x0701  # Number of retries
I2C_TIMEOUT = 0x0702  # Timeout
I2C_SLAVE = 0x0703  # Use this slave address
I2C_SLAVE_FORCE = 0x0706  # Use this slave address, even if it is already in use by a driver!
I2C_TENBIT = 0x0704  # 0 for 7 bit addrs, != 0 for 10 bit
# NOTE: 10-bit address support is very limited
I2C_FUNCS = 0x0705  # Get the adapter functionality mask
I2C_RDWR = 0x0707  # Combined R/W transfer (one STOP only)
I2C_PEC = 0x0708  # != 0 to use PEC with SMBus
I2C_SMBUS = 0x0720  # SMBus transfer. Takes pointer to i2c_smbus_ioctl_data

# SMBus transfer read or write markers from uapi/linux/i2c.h
I2C_SMBUS_WRITE = 0
I2C_SMBUS_READ = 1

# Size identifiers uapi/linux/i2c.h
I2C_SMBUS_QUICK = 0
I2C_SMBUS_BYTE = 1
I2C_SMBUS_BYTE_DATA = 2
I2C_SMBUS_WORD_DATA = 3
I2C_SMBUS_PROC_CALL = 4
I2C_SMBUS_BLOCK_DATA = 5
# NOTE: I2c_SMBUS_BLOCK_DATA isn't supported by Pure-I2C drivers with
# SMBUS emulation, like those in RaspberryPi, OrangePi, etc.
I2C_SMBUS_BLOCK_PROC_CALL = 7
# Like I2C_SMBUS_BLOCK_DATA, it isn't supported by Pure-I2C drivers either.
I2C_SMBUS_I2C_BLOCK_DATA = 8
I2C_SMBUS_BLOCK_MAX = 32

# To determine what functionality is present (uapi/linux/i2c.h)


class I2cFunc(IntFlag):
    """
    These flags identify the operations supported by an I2C/SMBus device.

    You can test these flags on your `smbus.funcs`
    """

    I2C = 0x00000001
    ADDR_10BIT = 0x00000002
    PROTOCOL_MANGLING = 0x00000004  # I2C_M_IGNORE_NAK etc.
    SMBUS_PEC = 0x00000008
    NOSTART = 0x00000010  # I2C_M_NOSTART
    SLAVE = 0x00000020
    SMBUS_BLOCK_PROC_CALL = 0x00008000  # SMBus 2.0
    SMBUS_QUICK = 0x00010000
    SMBUS_READ_BYTE = 0x00020000
    SMBUS_WRITE_BYTE = 0x00040000
    SMBUS_READ_BYTE_DATA = 0x00080000
    SMBUS_WRITE_BYTE_DATA = 0x00100000
    SMBUS_READ_WORD_DATA = 0x00200000
    SMBUS_WRITE_WORD_DATA = 0x00400000
    SMBUS_PROC_CALL = 0x00800000
    SMBUS_READ_BLOCK_DATA = 0x01000000
    SMBUS_WRITE_BLOCK_DATA = 0x02000000
    SMBUS_READ_I2C_BLOCK = 0x04000000  # I2C-like block xfer
    SMBUS_WRITE_I2C_BLOCK = 0x08000000  # w/ 1-byte reg. addr.
    SMBUS_HOST_NOTIFY = 0x10000000

    SMBUS_BYTE = 0x00060000
    SMBUS_BYTE_DATA = 0x00180000
    SMBUS_WORD_DATA = 0x00600000
    SMBUS_BLOCK_DATA = 0x03000000
    SMBUS_I2C_BLOCK = 0x0C000000
    SMBUS_EMUL = 0x0EFF0008


# i2c_msg flags from uapi/linux/i2c.h
I2C_M_RD = 0x0001
I2C_M_WR = 0x0000
I2C_M_TEN = 0x0010


class I2C_M_Bitflag(IntFlag):
    """
    These flags identify the operations to perform with
    a specific i2c_msg.
    """

    I2C_M_RD = 0x0001
    I2C_M_WR = 0x0000
    I2C_M_TEN = 0x0010
    I2C_M_RD_TEN = I2C_M_RD ^ I2C_M_TEN
    I2C_M_WR_TEN = I2C_M_WR ^ I2C_M_TEN


# Pointer definitions
LP_c_uint8 = POINTER(c_uint8)
LP_c_uint16 = POINTER(c_uint16)
LP_c_uint32 = POINTER(c_uint32)


i2c_smbus_data = c_uint8 * (I2C_SMBUS_BLOCK_MAX + 2)
"""
Adaptation of the i2c_smbus_data union in ``i2c.h``.
Data for SMBus messages.

Add two additional blocks, one for length, one for user-space
compatibility.
"""


class union_i2c_smbus_data(Union):
    """
    C union for representing i2c smbus data.
    """

    _fields_ = [("byte", c_uint8), ("word", c_uint16), ("block", i2c_smbus_data)]

    def __repr__(self):
        return (
            "<smbus3.smbus3.union_i2c_smbus_data "
            f"byte: {self.byte} word: {self.word} block: {self.block}>"
        )


union_pointer_type = POINTER(union_i2c_smbus_data)


class i2c_smbus_ioctl_data(Structure):
    """
    As defined in ``i2c-dev.h``.
    """

    _fields_ = [
        ("read_write", c_uint8),
        ("command", c_uint8),
        ("size", c_uint32),
        ("data", union_pointer_type),
    ]
    __slots__ = [name for name, type in _fields_]

    def __repr__(self):
        return (
            "<smbus3.smbus3.i2c_smbus_ioctl_data "
            f"read_write: {self.read_write} command: {self.command} "
            f"size: {self.size} data: {self.data.contents!r}>"
        )

    @staticmethod
    def create(read_write=I2C_SMBUS_READ, command=0, size=I2C_SMBUS_BYTE_DATA):
        """
        Create a new i2c_smbus_ioctl_data struct.
        """
        u = union_i2c_smbus_data()
        return i2c_smbus_ioctl_data(
            read_write=read_write,
            command=command,
            size=size,
            data=union_pointer_type(u),
        )


class i2c_msg(Structure):
    """
    As defined in ``i2c.h``.

    :ivar addr: i2c address
    :vartype addr: c_uint16
    :ivar flags: bit flags
    :vartype flags: c_uint16
    :ivar len: length
    :vartype len: c_uint16
    :ivar buf: data buffer
    :vartype buf: POINTER(c_char)
    """

    _fields_ = [
        ("addr", c_uint16),
        ("flags", c_uint16),
        ("len", c_uint16),
        ("buf", POINTER(c_char)),
    ]

    def __iter__(self):
        """
        Iterator / Generator

        :return: iterates over :py:attr:`buf`
        :rtype: :py:class:`generator` which returns int values
        """
        idx = 0
        while idx < self.len:
            yield ord(self.buf[idx])
            idx += 1

    def __len__(self):
        return self.len

    def __bytes__(self):
        return string_at(self.buf, self.len)

    def __repr__(self):
        return f"i2c_msg({self.addr:d},{self.flags:x},{self.__bytes__()!r})"

    def __str__(self):
        """
        Return a string, discarding non decodable bytes.

        :return: string of i2c_msg.__bytes__()
        :rtype: str
        """
        s = self.__bytes__()
        # Throw away non-decodable bytes
        s = s.decode(errors="ignore")
        return s

    @staticmethod
    def read(address, length, flags=I2C_M_RD):
        """
        Prepares an i2c read transaction.

        :param address: Slave address.
        :type: address: int
        :param length: Number of bytes to read.
        :type: length: int
        :param flags: bitflags to pass (default: I2C_M_RD)
        :type flags: int
        :return: New :py:class:`i2c_msg` instance for read operation.
        :rtype: :py:class:`i2c_msg`
        """
        arr = create_string_buffer(length)
        return i2c_msg(addr=address, flags=flags, len=length, buf=arr)

    @staticmethod
    def write(address, buf, flags=I2C_M_WR):
        """
        Prepares an i2c write transaction.

        :param address: Slave address.
        :type address: int
        :param buf: Bytes to write. Either list of values or str.
        :type buf: list
        :param flags: bitflags to pass (default: I2C_M_WR)
        :type flags: int
        :return: New :py:class:`i2c_msg` instance for write operation.
        :rtype: :py:class:`i2c_msg`
        """
        if isinstance(buf, str):
            buf = bytes(map(ord, buf))
        else:
            buf = bytes(buf)
        arr = create_string_buffer(buf, len(buf))
        return i2c_msg(addr=address, flags=flags, len=len(arr), buf=arr)


class i2c_rdwr_ioctl_data(Structure):
    """
    As defined in ``i2c-dev.h``.

    Fields:
        msgs  - POINTER(i2c_msg)

        nmsgs - c_uint32
    """

    _fields_ = [("msgs", POINTER(i2c_msg)), ("nmsgs", c_uint32)]
    __slots__ = [name for name, type in _fields_]

    @staticmethod
    def create(*i2c_msg_instances):
        """
        Factory method for creating a i2c_rdwr_ioctl_data struct that can
        be called with ``ioctl(fd, I2C_RDWR, data)``.

        :param i2c_msg_instances: Up to 42 i2c_msg instances
        :rtype: i2c_rdwr_ioctl_data
        """
        n_msg = len(i2c_msg_instances)
        msg_array = (i2c_msg * n_msg)(*i2c_msg_instances)
        return i2c_rdwr_ioctl_data(msgs=msg_array, nmsgs=n_msg)


class SMBus:
    """
    The main SMBus class.
    """

    def __init__(self, bus=None, force=False):
        """
        Initialize and (optionally) open an i2c bus connection.

        :param bus: i2c bus number (e.g. 0 or 1)
            or an absolute file path (e.g. `/dev/i2c-42`).
            If not given, a subsequent  call to ``open()`` is required.
        :type bus: int or str
        :param force: force using the slave address even when driver is
            already using it.
        :type force: boolean
        """
        self.fd = None
        self.funcs = I2cFunc(0)
        if bus is not None:
            self.open(bus)
        self.address = None
        self.force = force
        self._force_last = None
        self._pec = 0
        self._tenbit = 0

    def __enter__(self):
        """Enter handler."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit handler."""
        self.close()

    def open(self, bus):
        """
        Open a given i2c bus.

        :param bus: i2c bus number (e.g. 0 or 1)
            or an absolute file path (e.g. '/dev/i2c-42').
        :type bus: int or str
        :raise TypeError: if type(bus) is not in (int, str)
        :rtype: None
        """
        if isinstance(bus, int):
            filepath = f"/dev/i2c-{bus}"
        elif isinstance(bus, str):
            filepath = bus
        else:
            raise TypeError(f"Unexpected type(bus)={type(bus)}")

        self.fd = os.open(filepath, os.O_RDWR)
        self.funcs = self._get_funcs()

    def close(self):
        """
        Close the i2c connection.

        :raise OSError: if the file descriptor in self.fd does not exist
        :rtype: None
        """
        if self.fd:
            os.close(self.fd)
            self.fd = None
            self._pec = 0
            self._tenbit = 0
            self.address = None
            self._force_last = None

    def _get_pec(self):
        return self._pec

    def enable_pec(self, enable=True):
        """
        Enable/Disable PEC (Packet Error Checking) - SMBus 1.1 and later

        :param enable: Whether to enable PEC or not.
        :type enable: bool
        :raise IOError: if SMBUS_PEC is not supported.
        :rtype: None
        """
        if not (self.funcs & I2cFunc.SMBUS_PEC):
            raise OSError("SMBUS_PEC is not a feature")
        self._pec = int(enable)
        ioctl(self.fd, I2C_PEC, self._pec)

    pec = property(_get_pec, enable_pec)  # Drop-in replacement for smbus member "pec"
    """Get and set SMBus PEC. 0 = disabled (default), 1 = enabled."""

    def _get_tenbit(self):
        return self._tenbit

    def enable_tenbit(self, enable=True):
        """
        Enable 10 bit addresses if they are supported.

        :param enable: Whether to enable 10bit addresses or not.
        :type enable: bool
        :raise IOError: if ADDR_10BIT is not supported.
        :rtype: None
        """
        if not (self.funcs & I2cFunc.ADDR_10BIT):
            raise OSError("ADDR_10BIT is not a feature")
        self._tenbit = int(enable)
        ioctl(self.fd, I2C_TENBIT, self._tenbit)

    tenbit = property(_get_tenbit, enable_tenbit)
    """Get and set 10bit addressing. 0 = disabled (default), 1 = enabled."""

    def _get_timeout(self):
        return self._timeout

    def set_timeout(self, timeout):
        """
        Set the timeout in units of 10ms.

        :param timeout: timeout as positive int in units of 10ms.
        :type timeout: int
        :rtype: None
        """
        self._timeout = timeout
        ioctl(self.fd, I2C_TIMEOUT, self._timeout)

    timeout = property(_get_timeout, set_timeout)
    """Get and set I2C timeout in units of 10ms."""

    def _get_retries(self):
        return self._retries

    def set_retries(self, retries):
        """
        Set the retries.

        :param retries: retries as positive int.
        :type retries: int
        :rtype: None
        """
        self._retries = retries
        ioctl(self.fd, I2C_RETRIES, self._retries)

    retries = property(_get_retries, set_retries)
    """Get and set I2C retries."""

    def _set_address(self, address, force=None):
        """
        Set i2c slave address to use for subsequent calls.
        Private.

        :param address:
        :type address: int
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :rtype: None
        """
        force = force if force is not None else self.force
        if self.address != address or self._force_last != force:
            if force is True:
                ioctl(self.fd, I2C_SLAVE_FORCE, address)
            else:
                ioctl(self.fd, I2C_SLAVE, address)
            self.address = address
            self._force_last = force

    def _get_funcs(self):
        """
        Returns a 32-bit value stating supported I2C functions.
        Private.

        :rtype: int
        """
        f = c_uint32()
        ioctl(self.fd, I2C_FUNCS, f)
        return f.value

    def write_quick(self, i2c_addr, force=None):
        """
        Perform quick transaction. Throws IOError if unsuccessful.

        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :raise IOError: if write is unsuccessful.
        :rtype: None
        """
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(
            read_write=I2C_SMBUS_WRITE, command=0, size=I2C_SMBUS_QUICK
        )
        ioctl(self.fd, I2C_SMBUS, msg)

    def read_byte(self, i2c_addr, force=None):
        """
        Read a single byte from a device.

        :rtype: int
        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :return: Read byte value
        :rtype: int
        """
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(read_write=I2C_SMBUS_READ, command=0, size=I2C_SMBUS_BYTE)
        ioctl(self.fd, I2C_SMBUS, msg)
        return msg.data.contents.byte

    def write_byte(self, i2c_addr, value, force=None):
        """
        Write a single byte to a device.

        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param value: value to write
        :type value: int
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :rtype: None
        """
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(
            read_write=I2C_SMBUS_WRITE, command=value, size=I2C_SMBUS_BYTE
        )
        ioctl(self.fd, I2C_SMBUS, msg)

    def read_byte_data(self, i2c_addr, register, force=None):
        """
        Read a single byte from a designated register.

        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param register: Register to read
        :type register: int
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :return: Read byte value
        :rtype: int
        """
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(
            read_write=I2C_SMBUS_READ, command=register, size=I2C_SMBUS_BYTE_DATA
        )
        ioctl(self.fd, I2C_SMBUS, msg)
        return msg.data.contents.byte

    def write_byte_data(self, i2c_addr, register, value, force=None):
        """
        Write a byte to a given register.

        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param register: Register to write to
        :type register: int
        :param value: Byte value to transmit
        :type value: int
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :rtype: None
        """
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(
            read_write=I2C_SMBUS_WRITE, command=register, size=I2C_SMBUS_BYTE_DATA
        )
        msg.data.contents.byte = value
        ioctl(self.fd, I2C_SMBUS, msg)

    def read_word_data(self, i2c_addr, register, force=None):
        """
        Read a single word (2 bytes) from a given register.

        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param register: Register to read
        :type register: int
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :return: 2-byte word
        :rtype: int
        """
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(
            read_write=I2C_SMBUS_READ, command=register, size=I2C_SMBUS_WORD_DATA
        )
        ioctl(self.fd, I2C_SMBUS, msg)
        return msg.data.contents.word

    def write_word_data(self, i2c_addr, register, value, force=None):
        """
        Write a single word (2 bytes) to a given register.

        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param register: Register to write to
        :type register: int
        :param value: Word value to transmit
        :type value: int
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :rtype: None
        """
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(
            read_write=I2C_SMBUS_WRITE, command=register, size=I2C_SMBUS_WORD_DATA
        )
        msg.data.contents.word = value
        ioctl(self.fd, I2C_SMBUS, msg)

    def process_call(self, i2c_addr, register, value, force=None):
        """
        Executes a SMBus Process Call, sending a 16-bit value and receiving a 16-bit response

        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param register: Register to read/write to
        :type register: int
        :param value: Word value to transmit
        :type value: int
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :rtype: int
        """
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(
            read_write=I2C_SMBUS_WRITE, command=register, size=I2C_SMBUS_PROC_CALL
        )
        msg.data.contents.word = value
        ioctl(self.fd, I2C_SMBUS, msg)
        return msg.data.contents.word

    def read_block_data(self, i2c_addr, register, force=None):
        """
        Read a block of up to 32-bytes from a given register.

        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param register: Start register
        :type register: int
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :return: List of bytes
        :rtype: list
        """
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(
            read_write=I2C_SMBUS_READ, command=register, size=I2C_SMBUS_BLOCK_DATA
        )
        ioctl(self.fd, I2C_SMBUS, msg)
        length = msg.data.contents.block[0]
        return msg.data.contents.block[1 : length + 1]

    def write_block_data(self, i2c_addr, register, data, force=None):
        """
        Write a block of byte data to a given register.

        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param register: Start register
        :type register: int
        :param data: List of bytes
        :type data: list
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :raise ValueError: if length of data in bytes is > I2C_SMBUS_BLOCK_MAX
        :rtype: None
        """
        length = len(data)
        if length > I2C_SMBUS_BLOCK_MAX:
            raise ValueError(f"Data length cannot exceed {I2C_SMBUS_BLOCK_MAX:d} bytes")
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(
            read_write=I2C_SMBUS_WRITE, command=register, size=I2C_SMBUS_BLOCK_DATA
        )
        msg.data.contents.block[0] = length
        msg.data.contents.block[1 : length + 1] = data
        ioctl(self.fd, I2C_SMBUS, msg)

    def block_process_call(self, i2c_addr, register, data, force=None):
        """
        Executes a SMBus Block Process Call, sending a variable-size data
        block and receiving another variable-size response

        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param register: Register to read/write to
        :type register: int
        :param data: List of bytes
        :type data: list
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :raise ValueError: if length of data in bytes is > I2C_SMBUS_BLOCK_MAX
        :return: List of bytes
        :rtype: list
        """
        length = len(data)
        if length > I2C_SMBUS_BLOCK_MAX:
            raise ValueError(f"Data length cannot exceed {I2C_SMBUS_BLOCK_MAX:d} bytes")
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(
            read_write=I2C_SMBUS_WRITE, command=register, size=I2C_SMBUS_BLOCK_PROC_CALL
        )
        msg.data.contents.block[0] = length
        msg.data.contents.block[1 : length + 1] = data
        ioctl(self.fd, I2C_SMBUS, msg)
        length = msg.data.contents.block[0]
        return msg.data.contents.block[1 : length + 1]

    def read_i2c_block_data(self, i2c_addr, register, length, force=None):
        """
        Read a block of byte data from a given register.

        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param register: Start register
        :type register: int
        :param length: Desired block length
        :type length: int
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :raise ValueError: if length (in bytes) is > I2C_SMBUS_BLOCK_MAX
        :return: List of bytes
        :rtype: list
        """
        if length > I2C_SMBUS_BLOCK_MAX:
            raise ValueError(f"Data length cannot exceed {I2C_SMBUS_BLOCK_MAX:d} bytes")
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(
            read_write=I2C_SMBUS_READ, command=register, size=I2C_SMBUS_I2C_BLOCK_DATA
        )
        msg.data.contents.byte = length
        ioctl(self.fd, I2C_SMBUS, msg)
        return msg.data.contents.block[1 : length + 1]

    def write_i2c_block_data(self, i2c_addr, register, data, force=None):
        """
        Write a block of byte data to a given register.

        :param i2c_addr: i2c address
        :type i2c_addr: int
        :param register: Start register
        :type register: int
        :param data: List of bytes
        :type data: list
        :param force: force using the slave address even when driver is already using it.
        :type force: bool
        :raise ValueError: if length of data in bytes is > I2C_SMBUS_BLOCK_MAX
        :rtype: None
        """
        length = len(data)
        if length > I2C_SMBUS_BLOCK_MAX:
            raise ValueError(f"Data length cannot exceed {I2C_SMBUS_BLOCK_MAX:d} bytes")
        self._set_address(i2c_addr, force=force)
        msg = i2c_smbus_ioctl_data.create(
            read_write=I2C_SMBUS_WRITE, command=register, size=I2C_SMBUS_I2C_BLOCK_DATA
        )
        msg.data.contents.block[0] = length
        msg.data.contents.block[1 : length + 1] = data
        ioctl(self.fd, I2C_SMBUS, msg)

    def i2c_rdwr(self, *i2c_msgs):
        """
        Combine a series of i2c read and write operations in a single
        transaction (with repeated start bits but no stop bits in between).

        This method takes i2c_msg instances as input, which must be created
        first with :py:meth:`i2c_msg.read` or :py:meth:`i2c_msg.write`.

        :param i2c_msgs: One or more i2c_msg class instances.
        :type i2c_msgs: i2c_msg
        :rtype: None
        """
        ioctl_data = i2c_rdwr_ioctl_data.create(*i2c_msgs)
        ioctl(self.fd, I2C_RDWR, ioctl_data)

    def i2c_rd(self, i2c_addr, length, flags=I2C_M_RD):
        """
        Perform a single i2c read operation, given an i2c_addr and length.

        :param i2c_addr: i2c address for the read operation.
        :type i2c_addr: int
        :param length: length of read.
        :type length: int
        :param flags: bitflags to pass (default: I2C_M_RD)
        :type flags: int
        :rtype: i2c_msg
        """
        msg = i2c_msg.read(i2c_addr, length, flags=flags)
        self.i2c_rdwr(msg)
        return msg

    def i2c_wr(self, i2c_addr, buf, flags=I2C_M_WR):
        """
        Perform a single i2c write operation, given an i2c_addr and a
        buffer to copy.

        :param i2c_addr: i2c address for the write operation.
        :type i2c_addr: int
        :param buf: buffer to write.
        :type buf: list
        :param flags: bitflags to pass (default: I2C_M_WR)
        :type flags: int
        :rtype: i2c_msg
        """
        msg = i2c_msg.write(i2c_addr, buf, flags=flags)
        self.i2c_rdwr(msg)
        return msg
