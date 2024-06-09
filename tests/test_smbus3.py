"""
tests/test_smbus3.py
--------------------

Main tests for SMBus class, i2c_msg, and I2cFunc.
"""

import unittest
from unittest import mock

from smbus3 import I2cFunc, SMBus, i2c_msg

##########################################################################
# Mock open, close and ioctl so we can run our unit tests anywhere.

# Required I2C constant definitions repeated
I2C_FUNCS = 0x0705  # Get the adapter functionality mask
I2C_SMBUS = 0x0720
I2C_SMBUS_WRITE = 0
I2C_SMBUS_READ = 1

I2C_SMBUS_QUICK = 0
I2C_SMBUS_BYTE_DATA = 2
I2C_SMBUS_WORD_DATA = 3
I2C_SMBUS_BLOCK_DATA = 5  # Can't get this one to work on my Raspberry Pi
I2C_SMBUS_I2C_BLOCK_DATA = 8
I2C_SMBUS_BLOCK_MAX = 32

MOCK_FD = "Mock file descriptor"
MOCK_I2C_FUNC = 0xEFF0001

# Test buffer for read operations
test_buffer = [x for x in range(256)]


def mock_open(*args):
    print(f"Mocking open: {args[0]}")
    return MOCK_FD


def mock_close(*args):
    print("Mocking close")
    assert args[0] == MOCK_FD


def mock_ioctl(fd, command, msg):
    print(f"Mocking ioctl with command 0x{command:X} and msg {msg}")
    assert fd == MOCK_FD
    assert command is not None
    assert isinstance(command, int)

    # Reproduce i2c capability of a Raspberry Pi 3 w/o PEC support
    if command == I2C_FUNCS:
        msg.value = MOCK_I2C_FUNC
        print(f"Setting msg val: 0x{msg.value:X}")
        return

    # Reproduce ioctl read operations
    if command == I2C_SMBUS and msg.read_write == I2C_SMBUS_READ:
        offset = msg.command
        if msg.size == I2C_SMBUS_BYTE_DATA:
            msg.data.contents.byte = test_buffer[offset]
        elif msg.size == I2C_SMBUS_WORD_DATA:
            msg.data.contents.word = test_buffer[offset + 1] * 256 + test_buffer[offset]
        elif msg.size == I2C_SMBUS_I2C_BLOCK_DATA:
            for k in range(msg.data.contents.byte):
                msg.data.contents.block[k + 1] = test_buffer[offset + k]

    # Reproduce a failing Quick write transaction
    if command == I2C_SMBUS and msg.read_write == I2C_SMBUS_WRITE and msg.size == I2C_SMBUS_QUICK:
        raise OSError("Mocking SMBus Quick failed")


# Override open, close, read, and ioctl with our mock functions
open_mock = mock.patch("smbus3.smbus3.os.open", mock_open)
close_mock = mock.patch("smbus3.smbus3.os.close", mock_close)
ioctl_mock = mock.patch("smbus3.smbus3.ioctl", mock_ioctl)
##########################################################################

# Common error messages
INCORRECT_LENGTH_MSG = "Result array of incorrect length."


class SMBusTestCase(unittest.TestCase):
    def setUp(self):
        open_mock.start()
        close_mock.start()
        ioctl_mock.start()

    def tearDown(self):
        open_mock.stop()
        close_mock.stop()
        ioctl_mock.stop()


# Test cases
class TestSMBus(SMBusTestCase):
    def test_func(self):
        bus = SMBus(1)
        print(f"Supported I2C functionality: 0x{bus.funcs:X}")
        self.assertEqual(bus.funcs, MOCK_I2C_FUNC)
        bus.close()

    def test_enter_exit(self):
        for idx in (1, "/dev/i2c-alias"):
            with SMBus(idx) as bus:
                self.assertIsNotNone(bus.fd)
            self.assertIsNone(bus.fd, None)

        with SMBus() as bus:
            self.assertIsNone(bus.fd)
            bus.open(2)
            self.assertIsNotNone(bus.fd)
        self.assertIsNone(bus.fd)

    def test_open_close(self):
        for idx in (1, "/dev/i2c-alias"):
            bus = SMBus()
            self.assertIsNone(bus.fd)
            bus.open(idx)
            self.assertIsNotNone(bus.fd)
            bus.close()
            self.assertIsNone(bus.fd)

    def test_write(self):
        bus = SMBus(1)
        # Write byte:
        bus.write_byte(80, 0x001, force=False)
        # Write byte - force = True
        bus.write_byte(80, 0x001, force=True)
        # Write word data:
        bus.write_word_data(80, 1, 0x001, force=False)
        # Process call:
        self.assertEqual(bus.process_call(80, 1, 0x001), 1)
        bus.close()

    def test_read(self):
        res = []
        res2 = []
        res3 = []
        res4 = []
        res5 = []

        bus = SMBus(1)

        # Read bytes
        for k in range(2):
            x = bus.read_byte_data(80, k)
            res.append(x)
        self.assertEqual(len(res), 2, msg=INCORRECT_LENGTH_MSG)

        # Read word
        x = bus.read_word_data(80, 0)
        res2.append(x & 255)
        res2.append(x / 256)
        self.assertEqual(len(res2), 2, msg=INCORRECT_LENGTH_MSG)
        self.assertListEqual(res, res2, msg="Byte and word reads differ")

        # Read block of N bytes
        n = 2
        x = bus.read_i2c_block_data(80, 0, n)
        res3.extend(x)
        self.assertEqual(len(res3), n, msg=INCORRECT_LENGTH_MSG)
        self.assertListEqual(res, res3, msg="Byte and block reads differ")

        # Read byte - force False
        for _ in range(2):
            x = bus.read_byte(80, force=False)
            res4.append(x)
        self.assertEqual(len(res4), 2, msg=INCORRECT_LENGTH_MSG)

        # Read byte - force True
        for _ in range(2):
            x = bus.read_byte(80, force=True)
            res5.append(x)
        self.assertEqual(len(res5), 2, msg=INCORRECT_LENGTH_MSG)

        bus.close()

    def test_quick(self):
        bus = SMBus(1)
        self.assertRaises(IOError, bus.write_quick, 80)

    def test_timeout(self):
        def set_timeout(bus, timeout=15):
            bus.timeout = timeout

        bus = SMBus(1)
        set_timeout(bus)

        self.assertEqual(bus._timeout, 15)
        self.assertEqual(bus._get_timeout(), 15)
        self.assertEqual(bus.timeout, 15)
        bus.close()

    def test_retries(self):
        def set_retries(bus, retries=3):
            bus.retries = retries

        bus = SMBus(1)
        set_retries(bus)

        self.assertEqual(bus._retries, 3)
        self.assertEqual(bus._get_retries(), 3)
        self.assertEqual(bus.retries, 3)
        bus.close()

    def test_pec(self):
        def set_pec(bus, enable=True):
            bus.pec = enable

        # Enabling PEC should fail (no mocked PEC support)
        bus = SMBus(1)
        self.assertRaises(IOError, set_pec, bus, True)
        self.assertRaises(IOError, set_pec, bus, 1)
        self.assertEqual(bus.pec, 0)

        # Ensure PEC status is reset by close()
        bus._pec = 1
        self.assertEqual(bus.pec, 1)
        bus.close()
        self.assertEqual(bus.pec, 0)


class TestSMBusWrapper(SMBusTestCase):
    """Similar test as TestSMBus except it encapsulates it all access within "with" blocks."""

    def test_func(self):
        with SMBus(1) as bus:
            print(f"Supported I2C functionality: 0x{bus.funcs:X}")
            self.assertTrue(bus.funcs & I2cFunc.I2C > 0)
            self.assertTrue(bus.funcs & I2cFunc.SMBUS_QUICK > 0)
            self.assertFalse(bus.funcs & I2cFunc.SMBUS_PEC > 0)

    def test_read(self):
        res = []
        res2 = []
        res3 = []

        # Read bytes
        with SMBus(1) as bus:
            for k in range(2):
                x = bus.read_byte_data(80, k)
                res.append(x)
        self.assertEqual(len(res), 2, msg=INCORRECT_LENGTH_MSG)

        # Read word
        with SMBus(1) as bus:
            x = bus.read_word_data(80, 0)
            res2.append(x & 255)
            res2.append(x / 256)
        self.assertEqual(len(res2), 2, msg=INCORRECT_LENGTH_MSG)
        self.assertListEqual(res, res2, msg="Byte and word reads differ")

        # Read block of N bytes
        n = 2
        with SMBus(1) as bus:
            x = bus.read_i2c_block_data(80, 0, n)
            res3.extend(x)
        self.assertEqual(len(res3), n, msg=INCORRECT_LENGTH_MSG)
        self.assertListEqual(res, res3, msg="Byte and block reads differ")


class TestI2CMsg(SMBusTestCase):
    def test_i2c_msg_rd(self):
        # 1: Convert message content to list
        msg = i2c_msg.read(60, 10)
        self.assertEqual(len(list(msg)), 10)

        # 2: Test dunder methods
        print(f"Testing dunder methods for i2c_msg: {msg.__repr__()}")
        self.assertEqual(str(msg), "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(
            repr(msg), "i2c_msg(60,1,b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00')"
        )
        self.assertEqual(bytes(msg), b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")

    def test_i2c_msg_wr(self):
        # 1: Convert message content to list
        msg = i2c_msg.write(60, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        data = list(msg)
        self.assertEqual(len(data), 10)

        # 2: i2c_msg is iterable
        k = 0
        s = 0
        for value in msg:
            k += 1
            s += value
        self.assertEqual(k, 10, msg="Incorrect length")
        self.assertEqual(s, 55, msg="Incorrect sum")

        # 3: Through i2c_msg properties
        s = 0
        for k in range(0, msg.len):
            s += ord(msg.buf[k])
        k += 1  # Convert to length
        self.assertEqual(k, 10, msg="Incorrect length")
        self.assertEqual(s, 55, msg="Incorrect sum")

        # 4: Test dunder methods
        print(f"Testing dunder methods for i2c_msg: {msg.__repr__()}")
        self.assertEqual(str(msg), "\x01\x02\x03\x04\x05\x06\x07\x08\t\n")
        self.assertEqual(
            repr(msg), "i2c_msg(60,0,b'\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n')"
        )
        self.assertEqual(bytes(msg), b"\x01\x02\x03\x04\x05\x06\x07\x08\t\n")

    def test_i2c_msg_wr_str(self):
        # 1: Convert message content to list
        msg = i2c_msg.write(60, "foo")
        data = list(msg)
        self.assertEqual(len(data), 3)

        # 2: i2c_msg is iterable
        k = 0
        s = 0
        for value in msg:
            k += 1
            s += value
        self.assertEqual(k, 3, msg="Incorrect length")
        self.assertEqual(s, 324, msg="Incorrect sum")

        # 3: Through i2c_msg properties
        s = 0
        for k in range(0, msg.len):
            s += ord(msg.buf[k])
        k += 1  # Convert to length
        self.assertEqual(k, 3, msg="Incorrect length")
        self.assertEqual(s, 324, msg="Incorrect sum")

        # 4: Test dunder methods
        print(f"Testing dunder methods for i2c_msg: {msg.__repr__()}")
        self.assertEqual(str(msg), "foo")
        self.assertEqual(repr(msg), "i2c_msg(60,0,b'foo')")
        self.assertEqual(bytes(msg), b"foo")


class TestI2CMsgRDWR(SMBusTestCase):
    def test_i2c_rdwr_single_rd(self):
        msg = i2c_msg.read(60, 10)
        self.assertEqual(len(list(msg)), 10)
        with SMBus(1) as bus:
            bus.i2c_rdwr(msg)

    def test_i2c_rdwr_single_wr(self):
        msg = i2c_msg.write(60, "foo")
        with SMBus(1) as bus:
            bus.i2c_rdwr(msg)

    def test_i2c_rdwr_multi(self):
        msg1 = i2c_msg.read(60, 10)
        msg2 = i2c_msg.write(60, "foo")
        msg3 = i2c_msg.write(60, "bar")
        msg4 = i2c_msg.write(60, "baz")
        with SMBus(1) as bus:
            bus.i2c_rdwr(msg1, msg2, msg3, msg4)

    def test_i2c_rd(self):
        with SMBus(1) as bus:
            bus.i2c_rd(60, 10)

    def test_i2c_wr(self):
        with SMBus(1) as bus:
            bus.i2c_wr(60, [1, 2, 3])
