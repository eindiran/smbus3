"""
tests/test_smbus3.py
--------------------

Main tests for SMBus class, i2c_msg, and I2cFunc.
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from smbus3 import I2C_M_Bitflag, I2cFunc, SMBus, i2c_msg

# Required I2C constant definitions repeated
I2C_FUNCS = 0x0705  # Get the adapter functionality mask
I2C_SMBUS = 0x0720
I2C_SMBUS_WRITE = 0
I2C_SMBUS_READ = 1

I2C_SMBUS_QUICK = 0
I2C_SMBUS_BYTE = 1
I2C_SMBUS_BYTE_DATA = 2
I2C_SMBUS_WORD_DATA = 3
I2C_SMBUS_BLOCK_DATA = 5
I2C_SMBUS_I2C_BLOCK_DATA = 8
I2C_SMBUS_BLOCK_MAX = 32

MOCK_FD = "Mock file descriptor"
MOCK_I2C_FUNC_LIMITED = 0xEFF0001
MOCK_I2C_FUNC_FULL = 0xEFF000B
MOCK_MSG = None

# Test buffer for read operations
test_buffer = [x for x in range(256)]


def mock_msg_refresh(msg):
    """
    Cleanup the mock msg used for writes.
    """
    global MOCK_MSG  # noqa
    MOCK_MSG = msg


# Mock open, close and ioctl so we can run our unit tests anywhere.
def mock_open(*args):
    print(f"Mocking open: {args[0]}")
    return MOCK_FD


def mock_close(*args):
    print("Mocking close")
    assert args[0] == MOCK_FD


def mock_ioctl_limited(fd, command, msg):
    print(f"Mocking ioctl with command 0x{command:X} and msg {msg}")
    assert fd == MOCK_FD
    assert command is not None
    assert isinstance(command, int)

    # Reproduce i2c capability of a Raspberry Pi 3 w/o PEC support and w/o
    # 10bit addressing support
    if command == I2C_FUNCS:
        msg.value = MOCK_I2C_FUNC_LIMITED
        print(f"Setting msg val: 0x{msg.value:X}")
        return

    # Reproduce ioctl read operations
    if command == I2C_SMBUS and msg.read_write == I2C_SMBUS_READ:
        offset = msg.command
        if msg.size == I2C_SMBUS_BYTE:
            msg.data.contents.byte = test_buffer[offset]
        elif msg.size == I2C_SMBUS_BYTE_DATA:
            msg.data.contents.byte = test_buffer[offset]
        elif msg.size == I2C_SMBUS_WORD_DATA:
            msg.data.contents.word = test_buffer[offset + 1] * 256 + test_buffer[offset]
        elif msg.size == I2C_SMBUS_I2C_BLOCK_DATA:
            for k in range(msg.data.contents.byte):
                msg.data.contents.block[k + 1] = test_buffer[offset + k]
        elif msg.size == I2C_SMBUS_BLOCK_DATA:
            msg.data.contents.block[0] = 32
            for k in range(32):
                msg.data.contents.block[k + 1] = test_buffer[offset + k]

    # Reproduce ioctl write operations
    if command == I2C_SMBUS and msg.read_write == I2C_SMBUS_WRITE:
        mock_msg_refresh(msg)

    # Reproduce a failing Quick write transaction
    if command == I2C_SMBUS and msg.read_write == I2C_SMBUS_WRITE and msg.size == I2C_SMBUS_QUICK:
        raise OSError("Mocking SMBus Quick failed")


def mock_ioctl_full(fd, command, msg):
    print(f"Mocking ioctl with command 0x{command:X} and msg {msg}")
    assert fd == MOCK_FD
    assert command is not None
    assert isinstance(command, int)

    # Reproduce i2c capability w/ PEC support and w/
    # 10bit addressing support
    if command == I2C_FUNCS:
        msg.value = MOCK_I2C_FUNC_FULL
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
        elif msg.size == I2C_SMBUS_BLOCK_DATA:
            msg.data.contents.block[0] = 32
            for k in range(32):
                msg.data.contents.block[k + 1] = test_buffer[offset + k]

    # Reproduce ioctl write operations
    if command == I2C_SMBUS and msg.read_write == I2C_SMBUS_WRITE:
        mock_msg_refresh(msg)


# Override open, close, read, and ioctl with our mock functions
open_mock = mock.patch("smbus3.smbus3.os.open", mock_open)
close_mock = mock.patch("smbus3.smbus3.os.close", mock_close)
ioctl_limited_mock = mock.patch("smbus3.smbus3.ioctl", mock_ioctl_limited)
ioctl_full_mock = mock.patch("smbus3.smbus3.ioctl", mock_ioctl_full)


@contextmanager
def switch_to_full_featured_ioctl_mock():
    """
    This context manager allows you to temporarily switch the I2C_FUNCS supported
    by the ioctl mock used in the test.
    """
    try:
        ioctl_limited_mock.stop()
        ioctl_full_mock.start()
        yield
    finally:
        ioctl_full_mock.stop()
        ioctl_limited_mock.start()


# Common error messages
INCORRECT_LENGTH_MSG = "Result array of incorrect length."


class SMBusTestCase(unittest.TestCase):
    def setUp(self):
        open_mock.start()
        close_mock.start()
        ioctl_limited_mock.start()

    def tearDown(self):
        open_mock.stop()
        close_mock.stop()
        ioctl_limited_mock.stop()


# Test cases
class TestSMBus(SMBusTestCase):
    def test_func(self):
        bus = SMBus(1)
        print(f"Supported I2C functionality: 0x{bus.funcs:X}")
        self.assertEqual(bus.funcs, MOCK_I2C_FUNC_LIMITED)
        bus.close()

        # Now try with full features:
        with switch_to_full_featured_ioctl_mock():
            bus = SMBus(1)
            print(f"Supported I2C functionality: 0x{bus.funcs:X}")
            self.assertEqual(bus.funcs, MOCK_I2C_FUNC_FULL)
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
        bus = SMBus()
        with self.assertRaises(TypeError):
            bus.open([1, 2])

    def test_write(self):  # noqa: PLR0915
        bus = SMBus(1)
        # Write byte:
        bus.write_byte(80, 0x001, force=False)
        self.assertEqual(MOCK_MSG.read_write, 0)
        self.assertEqual(MOCK_MSG.command, 1)
        self.assertEqual(MOCK_MSG.size, 1)
        mock_msg_refresh(None)
        # Write byte - force = True
        bus.write_byte(80, 0x001, force=True)
        self.assertEqual(MOCK_MSG.read_write, 0)
        self.assertEqual(MOCK_MSG.command, 1)
        self.assertEqual(MOCK_MSG.size, 1)
        mock_msg_refresh(None)
        # Write byte data
        bus.write_byte_data(80, 1, 0x001)
        self.assertEqual(MOCK_MSG.read_write, 0)
        self.assertEqual(MOCK_MSG.command, 1)
        self.assertEqual(MOCK_MSG.size, 2)
        self.assertEqual(MOCK_MSG.data.contents.byte, 1)
        self.assertEqual(MOCK_MSG.data.contents.word, 1)
        mock_msg_refresh(None)
        # Write word data:
        bus.write_word_data(80, 1, 0x001, force=False)
        self.assertEqual(MOCK_MSG.read_write, 0)
        self.assertEqual(MOCK_MSG.command, 1)
        self.assertEqual(MOCK_MSG.size, 3)
        self.assertEqual(MOCK_MSG.data.contents.byte, 1)
        self.assertEqual(MOCK_MSG.data.contents.word, 1)
        mock_msg_refresh(None)
        # Process call:
        self.assertEqual(bus.process_call(80, 1, 0x001), 1)
        self.assertEqual(MOCK_MSG.read_write, 0)
        self.assertEqual(MOCK_MSG.command, 1)
        self.assertEqual(MOCK_MSG.size, 4)
        self.assertEqual(MOCK_MSG.data.contents.byte, 1)
        self.assertEqual(MOCK_MSG.data.contents.word, 1)
        mock_msg_refresh(None)
        # Write block data:
        bus.write_block_data(80, 1, [1, 2, 3])
        self.assertEqual(MOCK_MSG.read_write, 0)
        self.assertEqual(MOCK_MSG.command, 1)
        self.assertEqual(MOCK_MSG.size, 5)
        self.assertEqual(MOCK_MSG.data.contents.byte, 3)
        self.assertEqual(MOCK_MSG.data.contents.word, 256 + 3)
        self.assertListEqual(list(MOCK_MSG.data.contents.block[1:4]), [1, 2, 3])
        mock_msg_refresh(None)
        with self.assertRaises(ValueError):
            # Try writing too large of a block
            x = [_ for _ in range(35)]
            bus.write_block_data(80, 1, x)
        # Write i2c block data:
        bus.write_i2c_block_data(80, 1, [1, 2, 3])
        self.assertEqual(MOCK_MSG.read_write, 0)
        self.assertEqual(MOCK_MSG.command, 1)
        self.assertEqual(MOCK_MSG.size, 8)
        self.assertEqual(MOCK_MSG.data.contents.byte, 3)
        self.assertEqual(MOCK_MSG.data.contents.word, 256 + 3)
        self.assertListEqual(list(MOCK_MSG.data.contents.block[1:4]), [1, 2, 3])
        mock_msg_refresh(None)
        with self.assertRaises(ValueError):
            # Try writing too large of a block
            x = [_ for _ in range(35)]
            bus.write_i2c_block_data(80, 1, x)
        # Block process call:
        x = [_ for _ in range(8)]
        self.assertEqual(bus.block_process_call(80, 1, x), x)
        with self.assertRaises(ValueError):
            # Try writing too large of a block
            x = [_ for _ in range(35)]
            bus.block_process_call(80, 1, x)
        bus.close()

    def test_read(self):
        res = []
        res2 = []
        res3 = []
        res4 = []
        res5 = []
        res6 = []

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

        # Read block of N bytes (i2c)
        n = 2
        x = bus.read_i2c_block_data(80, 0, n)
        res3.extend(x)
        self.assertEqual(len(res3), n, msg=INCORRECT_LENGTH_MSG)
        self.assertListEqual(res, res3, msg="Byte and block reads differ")

        # Check that reading too many bytes causes a ValueError:
        with self.assertRaises(ValueError):
            bus.read_i2c_block_data(80, 0, 35)

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

        # Read block of 32 bytes
        x = bus.read_block_data(80, 0)
        res6.extend(x)
        self.assertEqual(len(res6), 32, msg=INCORRECT_LENGTH_MSG)
        self.assertListEqual(res, res6[:2], msg="Byte and block reads differ")
        self.assertEqual(
            sum(res6), sum(_ for _ in range(32)), msg="Incorrect values from read_block_data"
        )

        bus.close()

    def test_write_full(self):
        """
        Test writes with 10bit + PEC enabled.
        """
        with switch_to_full_featured_ioctl_mock():
            bus = SMBus(1)
            bus.pec = 1
            bus.tenbit = 1
            # Write byte:
            bus.write_byte(80, 0x001, force=False)
            # Write byte - force = True
            bus.write_byte(80, 0x001, force=True)
            # Write byte data
            bus.write_byte_data(80, 1, 0x001)
            # Write word data:
            bus.write_word_data(80, 1, 0x001, force=False)
            # Process call:
            self.assertEqual(bus.process_call(80, 1, 0x001), 1)
            # Write block data:
            bus.write_block_data(80, 1, [1, 2, 3])
            with self.assertRaises(ValueError):
                # Try writing too large of a block
                x = [_ for _ in range(35)]
                bus.write_block_data(80, 1, x)
            # Write i2c block data:
            bus.write_i2c_block_data(80, 1, [1, 2, 3])
            with self.assertRaises(ValueError):
                # Try writing too large of a block
                x = [_ for _ in range(35)]
                bus.write_i2c_block_data(80, 1, x)
            # Block process call:
            x = [_ for _ in range(8)]
            self.assertEqual(bus.block_process_call(80, 1, x), x)
            with self.assertRaises(ValueError):
                # Try writing too large of a block
                x = [_ for _ in range(35)]
                bus.block_process_call(80, 1, x)
            bus.close()

    def test_read_full(self):
        """
        Test reads with 10bit + PEC enabled.
        """
        with switch_to_full_featured_ioctl_mock():
            res = []
            res2 = []
            res3 = []
            res4 = []
            res5 = []
            res6 = []

            bus = SMBus(1)
            bus.pec = 1
            bus.tenbit = 1

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

            # Read block of N bytes (i2c)
            n = 2
            x = bus.read_i2c_block_data(80, 0, n)
            res3.extend(x)
            self.assertEqual(len(res3), n, msg=INCORRECT_LENGTH_MSG)
            self.assertListEqual(res, res3, msg="Byte and block reads differ")

            # Check that reading too many bytes causes a ValueError:
            with self.assertRaises(ValueError):
                bus.read_i2c_block_data(80, 0, 35)

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

            # Read block of 32 bytes
            x = bus.read_block_data(80, 0)
            res6.extend(x)
            self.assertEqual(len(res6), 32, msg=INCORRECT_LENGTH_MSG)
            self.assertListEqual(res, res6[:2], msg="Byte and block reads differ")
            self.assertEqual(
                sum(res6), sum(_ for _ in range(32)), msg="Incorrect values from read_block_data"
            )

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

        # Test true enable by changing ioctl mock:
        with switch_to_full_featured_ioctl_mock():
            bus = SMBus(1)
            self.assertEqual(bus.pec, 0)
            set_pec(bus, enable=True)
            self.assertEqual(bus.pec, 1)
        bus.close()
        self.assertEqual(bus.pec, 0)

    def test_tenbit(self):
        def set_tenbit(bus, enable=True):
            bus.tenbit = enable

        # Enabling 10bit addressing should fail (no mocked support)
        bus = SMBus(1)
        self.assertRaises(IOError, set_tenbit, bus, True)
        self.assertRaises(IOError, set_tenbit, bus, 1)
        self.assertEqual(bus.tenbit, 0)

        bus._tenbit = 1
        self.assertEqual(bus.tenbit, 1)
        bus.close()
        self.assertEqual(bus.tenbit, 0)

        # Test true enable by changing ioctl mock:
        with switch_to_full_featured_ioctl_mock():
            bus = SMBus(1)
            self.assertEqual(bus.tenbit, 0)
            set_tenbit(bus, enable=True)
            self.assertEqual(bus.tenbit, 1)
        bus.close()
        self.assertEqual(bus.tenbit, 0)


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
            x = bus.i2c_rd(60, 10)
            self.assertTrue(x.flags & I2C_M_Bitflag.I2C_M_RD > 0)
            self.assertFalse(x.flags & I2C_M_Bitflag.I2C_M_TEN > 0)
            self.assertFalse(x.flags & I2C_M_Bitflag.I2C_M_WR > 0)
            # Test that we can set alternative bitflags:
            x = bus.i2c_rd(60, 10, flags=I2C_M_Bitflag.I2C_M_RD_TEN)
            self.assertTrue(x.flags & I2C_M_Bitflag.I2C_M_RD > 0)
            self.assertTrue(x.flags & I2C_M_Bitflag.I2C_M_TEN > 0)
            self.assertTrue(x.flags & I2C_M_Bitflag.I2C_M_RD_TEN > 0)
            self.assertFalse(x.flags & I2C_M_Bitflag.I2C_M_WR > 0)

    def test_i2c_wr(self):
        with SMBus(1) as bus:
            x = bus.i2c_wr(60, [1, 2, 3])
            self.assertFalse(x.flags & I2C_M_Bitflag.I2C_M_RD > 0)
            self.assertFalse(x.flags & I2C_M_Bitflag.I2C_M_TEN > 0)

            # Test that we can set alternative bitflags:
            x = bus.i2c_wr(60, [1, 2, 3], flags=I2C_M_Bitflag.I2C_M_WR_TEN)
            self.assertTrue(x.flags & I2C_M_Bitflag.I2C_M_TEN > 0)
            self.assertTrue(x.flags & I2C_M_Bitflag.I2C_M_WR_TEN > 0)
            self.assertFalse(x.flags & I2C_M_Bitflag.I2C_M_RD > 0)
