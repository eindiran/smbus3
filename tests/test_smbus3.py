"""
tests/test_smbus3.py
--------------------

Main tests for SMBus class, i2c_msg, and I2cFunc.
"""

import unittest

try:
    from unittest import mock
except ImportError:
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

# Test buffer for read operations
test_buffer = [x for x in range(256)]


def mock_open(*args):
    print(f"Mocking open: {args[0]}")
    return MOCK_FD


def mock_close(*args):
    assert args[0] == MOCK_FD


def mock_read(fd, length):
    assert fd == MOCK_FD
    return bytes(test_buffer[0:length])


def mock_ioctl(fd, command, msg):
    print("Mocking ioctl")
    assert fd == MOCK_FD
    assert command is not None

    # Reproduce i2c capability of a Raspberry Pi 3 w/o PEC support
    if command == I2C_FUNCS:
        msg.value = 0xEFF0001
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


# Override open, close and ioctl with our mock functions
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
        print(f"\nSupported I2C functionality: 0x{bus.funcs:X}")
        bus.close()

    def test_enter_exit(self):
        for id in (1, "/dev/i2c-alias"):
            with SMBus(id) as bus:
                self.assertIsNotNone(bus.fd)
            self.assertIsNone(bus.fd, None)

        with SMBus() as bus:
            self.assertIsNone(bus.fd)
            bus.open(2)
            self.assertIsNotNone(bus.fd)
        self.assertIsNone(bus.fd)

    def test_open_close(self):
        for id in (1, "/dev/i2c-alias"):
            bus = SMBus()
            self.assertIsNone(bus.fd)
            bus.open(id)
            self.assertIsNotNone(bus.fd)
            bus.close()
            self.assertIsNone(bus.fd)

    def test_read(self):
        res = []
        res2 = []
        res3 = []

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

        bus.close()

    def test_quick(self):
        bus = SMBus(1)
        self.assertRaises(IOError, bus.write_quick, 80)

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
            print(f"\nSupported I2C functionality: 0x{bus.funcs:X}")
            self.assertTrue(bus.funcs & I2cFunc.I2C > 0)
            self.assertTrue(bus.funcs & I2cFunc.SMBUS_QUICK > 0)

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
    def test_i2c_msg(self):
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
