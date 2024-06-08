from collections.abc import Iterable, Sequence
from ctypes import Array, Structure, Union, c_uint8, c_uint16, c_uint32, pointer
from enum import IntFlag
from types import TracebackType
from typing import SupportsBytes

I2C_SLAVE: int
I2C_SLAVE_FORCE: int
I2C_FUNCS: int
I2C_RDWR: int
I2C_SMBUS: int
I2C_PEC: int
I2C_SMBUS_WRITE: int
I2C_SMBUS_READ: int
I2C_SMBUS_QUICK: int
I2C_SMBUS_BYTE: int
I2C_SMBUS_BYTE_DATA: int
I2C_SMBUS_WORD_DATA: int
I2C_SMBUS_PROC_CALL: int
I2C_SMBUS_BLOCK_DATA: int
I2C_SMBUS_BLOCK_PROC_CALL: int
I2C_SMBUS_I2C_BLOCK_DATA: int
I2C_SMBUS_BLOCK_MAX: int

class I2cFunc(IntFlag):
    I2C = ...
    ADDR_10BIT = ...
    PROTOCOL_MANGLING = ...
    SMBUS_PEC = ...
    NOSTART = ...
    SLAVE = ...
    SMBUS_BLOCK_PROC_CALL = ...
    SMBUS_QUICK = ...
    SMBUS_READ_BYTE = ...
    SMBUS_WRITE_BYTE = ...
    SMBUS_READ_BYTE_DATA = ...
    SMBUS_WRITE_BYTE_DATA = ...
    SMBUS_READ_WORD_DATA = ...
    SMBUS_WRITE_WORD_DATA = ...
    SMBUS_PROC_CALL = ...
    SMBUS_READ_BLOCK_DATA = ...
    SMBUS_WRITE_BLOCK_DATA = ...
    SMBUS_READ_I2C_BLOCK = ...
    SMBUS_WRITE_I2C_BLOCK = ...
    SMBUS_HOST_NOTIFY = ...
    SMBUS_BYTE = ...
    SMBUS_BYTE_DATA = ...
    SMBUS_WORD_DATA = ...
    SMBUS_BLOCK_DATA = ...
    SMBUS_I2C_BLOCK = ...
    SMBUS_EMUL = ...

I2C_M_RD: int
LP_c_uint8: type[pointer[c_uint8]]
LP_c_uint16: type[pointer[c_uint16]]
LP_c_uint32: type[pointer[c_uint32]]

class i2c_smbus_data(Array): ...
class union_i2c_smbus_data(Union): ...

union_pointer_type: pointer[union_i2c_smbus_data]

class i2c_smbus_ioctl_data(Structure):
    @staticmethod
    def create(
        read_write: int = ..., command: int = ..., size: int = ...
    ) -> i2c_smbus_ioctl_data: ...

class i2c_msg(Structure):
    def __iter__(self) -> int: ...
    def __len__(self) -> int: ...
    def __bytes__(self) -> str: ...
    @staticmethod
    def read(address: int, length: int) -> i2c_msg: ...
    @staticmethod
    def write(address: int, buf: str | Iterable[int] | SupportsBytes) -> i2c_msg: ...

class i2c_rdwr_ioctl_data(Structure):
    @staticmethod
    def create(*i2c_msg_instances: Sequence[i2c_msg]) -> i2c_rdwr_ioctl_data: ...

class SMBus:
    fd: int = ...
    funcs: I2cFunc = ...
    address: int | None = ...
    force: bool | None = ...
    pec: int = ...
    def __init__(self, bus: None | int | str = ..., force: bool = ...) -> None: ...
    def __enter__(self) -> SMBus: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
    def open(self, bus: int | str) -> None: ...
    def close(self) -> None: ...
    def enable_pec(self, enable: bool) -> None: ...
    def write_quick(self, i2c_addr: int, force: bool | None = ...) -> None: ...
    def read_byte(self, i2c_addr: int, force: bool | None = ...) -> int: ...
    def write_byte(self, i2c_addr: int, value: int, force: bool | None = ...) -> None: ...
    def read_byte_data(self, i2c_addr: int, register: int, force: bool | None = ...) -> int: ...
    def write_byte_data(
        self, i2c_addr: int, register: int, value: int, force: bool | None = ...
    ) -> None: ...
    def read_word_data(self, i2c_addr: int, register: int, force: bool | None = ...) -> int: ...
    def write_word_data(
        self, i2c_addr: int, register: int, value: int, force: bool | None = ...
    ) -> None: ...
    def process_call(self, i2c_addr: int, register: int, value: int, force: bool | None = ...): ...
    def read_block_data(
        self, i2c_addr: int, register: int, force: bool | None = ...
    ) -> list[int]: ...
    def write_block_data(
        self,
        i2c_addr: int,
        register: int,
        data: Sequence[int],
        force: bool | None = ...,
    ) -> None: ...
    def block_process_call(
        self,
        i2c_addr: int,
        register: int,
        data: Sequence[int],
        force: bool | None = ...,
    ) -> list[int]: ...
    def read_i2c_block_data(
        self, i2c_addr: int, register: int, length: int, force: bool | None = ...
    ) -> list[int]: ...
    def write_i2c_block_data(
        self,
        i2c_addr: int,
        register: int,
        data: Sequence[int],
        force: bool | None = ...,
    ) -> None: ...
    def i2c_rdwr(self, *i2c_msgs: i2c_msg) -> None: ...
    def i2c_rd(self, i2c_addr: int, length: int) -> i2c_msg: ...
    def i2c_wr(self, i2c_addr: int, buf: Sequence[int]) -> None: ...
