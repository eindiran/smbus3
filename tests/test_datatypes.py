import unittest

from smbus3.smbus3 import (  # noqa: F401
    I2C_SMBUS_BLOCK_MAX,
    I2C_SMBUS_BYTE_DATA,
    I2C_SMBUS_READ,
    i2c_msg,
    i2c_rdwr_ioctl_data,
    i2c_smbus_ioctl_data,
    union_i2c_smbus_data,
)


class TestDataTypes(unittest.TestCase):
    def test_union_i2c_smbus_data(self):
        u = union_i2c_smbus_data()

        # Fill array with values 1, 2, ...
        for k in range(I2C_SMBUS_BLOCK_MAX + 2):
            u.block[k] = k + 1

        # Check that the union works
        self.assertEqual(u.byte, u.block[0], msg="Byte field differ")
        self.assertEqual(u.block[16], 17, msg="Array field does not match")

        # Set byte and se it reflected in the array
        u.byte = 255
        self.assertEqual(u.block[0], 255, msg="Byte field not reflected in array")

        # Reset array to zeros and check word field
        for k in range(I2C_SMBUS_BLOCK_MAX + 2):
            u.block[k] = 0
        u.word = 1607
        self.assertNotEqual(0, u.word, msg="Word field is zero but should be non-zero")
        u.word = 0

    def test_i2c_smbus_ioctl_data_factory(self):
        ioctl_msg = i2c_smbus_ioctl_data.create()

        self.assertEqual(ioctl_msg.read_write, I2C_SMBUS_READ)
        self.assertEqual(ioctl_msg.size, I2C_SMBUS_BYTE_DATA)

        # Simple test to check assignment
        ioctl_msg.data.contents.byte = 25
        self.assertEqual(ioctl_msg.data.contents.byte, 25, msg="Get not equal to set")

    def test_i2c_msg_read(self):
        msg = i2c_msg.read(80, 10)
        self.assertEqual(msg.addr, 80)
        self.assertEqual(msg.len, 10)
        self.assertEqual(msg.len, len(msg))
        self.assertEqual(msg.flags, 1)

    def test_i2c_msg_write(self):
        # Create from list
        buf = [65, 66, 67, 68, 1, 10, 255]
        msg = i2c_msg.write(81, buf)
        self.assertEqual(msg.addr, 81)
        self.assertEqual(msg.len, 7)
        self.assertEqual(msg.len, len(msg))
        self.assertEqual(msg.flags, 0)
        self.assertListEqual(buf, list(msg))
        # Create from str
        s = "ABCD\x01\n\xff"
        msg2 = i2c_msg.write(81, s)
        self.assertEqual(msg2.addr, msg.addr)
        self.assertEqual(msg2.len, msg.len)
        self.assertEqual(msg2.flags, msg.flags)
        self.assertListEqual(list(msg), list(msg2))
        self.assertEqual(str(msg2), "ABCD\x01\n")
        self.assertGreaterEqual(f"{msg2!r}".find(r"ABCD\x01\n\xff"), 0)

    def test_i2c_msg_iter(self):
        buf = [10, 11, 12, 13]
        msg = i2c_msg.write(81, buf)
        # Convert msg to list and compare
        msg_list = list(msg)
        self.assertListEqual(buf, msg_list)
        # Loop over each message entry
        i = 0
        for value in msg:
            self.assertEqual(value, buf[i])
            i += 1
        # Loop over with index and value
        for i, value in enumerate(msg):
            self.assertEqual(i + 10, value)
