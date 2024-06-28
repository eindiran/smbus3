
|build-and-test| |codeql| |docs| |coverage|

|versions| |package| |commits-since| |license|

.. |build-and-test| image:: https://github.com/eindiran/smbus3/actions/workflows/python-build-and-test.yml/badge.svg?branch=master
   :target: https://github.com/eindiran/smbus3/actions/workflows/python-build-and-test.yml
   :alt: Build and tests
.. |codeql| image:: https://github.com/eindiran/smbus3/actions/workflows/codeql-analysis.yml/badge.svg?branch=master
   :target: https://github.com/eindiran/smbus3/actions/workflows/codeql-analysis.yml
   :alt: CodeQL security analysis
.. |docs| image:: https://readthedocs.org/projects/smbus3/badge/?version=latest
   :target: https://smbus3.readthedocs.io/en/latest/
   :alt: Documentation
.. |coverage| image:: https://raw.githubusercontent.com/eindiran/smbus3/badges/.github/badges/coverage.svg
   :target: https://github.com/eindiran/smbus3/actions/workflows/coverage-master.yml
   :alt: Test coverage on master
.. |versions| image:: https://img.shields.io/pypi/pyversions/smbus3.svg
   :alt: Python versions
.. |package| image:: https://img.shields.io/pypi/v/smbus3.svg
   :target: ttps://pypi.org/project/smbus3/
   :alt: PyPI package
.. |commits-since| image:: https://img.shields.io/github/commits-since/eindiran/smbus3/latest.svg?color=green
   :target: https://github.com/eindiran/smbus3/releases/latest
   :alt: Commits on master since release
.. |license| image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://opensource.org/license/MIT
   :alt: MIT


What is `smbus3`
================


A drop-in replacement for `smbus2 <https://pypi.org/project/smbus2/>`__,
`smbus-cffi <https://pypi.org/project/smbus-cffi/>`__, or
`smbus-python <https://pypi.org/project/smbus/>`__ written in pure
Python and intended for use with Python 3.8+.

This library was forked from @kplindegaard’s excellent
`smbus2 <https://github.com/kplindegaard/smbus2>`__. If you need a
package that works with Python 2.7 - 3.7, smbus2 is the way to go.


Introduction
------------

smbus3 is a Python 3 implementation of the SMBus interface for use in
Python 3. It should be a drop-in replacement of both the original
`smbus package <https://pypi.org/project/smbus/>`__, the C-FFI
`smbus-cffi package <https://pypi.org/project/smbus-cffi/>`__ and
the pure Python `smbus2
package <https://pypi.org/project/smbus2/>`__. The interfaces will be
shared for backwards compatibility with ``smbus2``.

Currently supported features are:

-  Context manager-like control of ``SMBus`` objects
-  SMBus Packet Error Checking (PEC) support

  -  ``enable_pec()``

-  10bit addressing support

  -  ``enable_tenbit()``

-  Manual control over retries and timeouts

  -  ``set_retries()``
  -  ``set_timeout()``

-  Create raw ``i2c_msg`` messages
-  ``read_byte()``
-  ``write_byte()``
-  ``read_byte_data()``
-  ``write_byte_data()``
-  ``read_word_data()``
-  ``write_word_data()``
-  ``read_i2c_block_data()``
-  ``write_i2c_block_data()``
-  ``write_quick()``
-  ``process_call()``
-  ``read_block_data()``
-  ``write_block_data()``
-  ``block_process_call()``
-  ``i2c_rdwr()`` - *combined write/read transactions with repeated
   start*
-  ``i2c_rd()`` - single read via ``i2c_rdwr``
-  ``i2c_wr()`` - single write via ``i2c_rdwr``
-  Get i2c capabilities (``I2C_FUNCS``)

It is developed for Python 3.8+.

More information about updates and general changes are recorded in the
`change
log <https://github.com/eindiran/smbus3/blob/master/CHANGELOG.md>`__.

**NOTE:** this library leverages the ``ioctl`` syscall on Unix-like
operating systems. It **WILL NOT** work on Windows and Windows will
never be supported.

OSes leveraging the Linux kernel are the primary testbed for the
library, but if you try it out on \*BSD and find a bug or problem,
please `open an issue <https://github.com/eindiran/smbus3/issues>`__.

SMBus code examples
-------------------

smbus3 installs next to smbus / smbus2 as the package, so it’s not
really a 100% replacement. You must change the module name.

Example 1a: Read a byte
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   from smbus3 import SMBus

   # Open i2c bus 1 and read one byte from address 80, offset 0
   bus = SMBus(1)
   b = bus.read_byte_data(80, 0)
   print(b)
   bus.close()

Example 1b: Read a byte using ``with``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the very same example but safer to use since the ``SMBus``
object will be closed automatically when exiting the ``with`` block.

.. code:: python

   from smbus3 import SMBus

   with SMBus(1) as bus:
       b = bus.read_byte_data(80, 0)
       print(b)

Example 1c: Read a byte with PEC enabled
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Same example with Packet Error Checking enabled.

.. code:: python

   from smbus3 import SMBus

   with SMBus(1) as bus:
       bus.pec = 1  # Enable PEC
       b = bus.read_byte_data(80, 0)
       print(b)

Example 1d: Read a byte with 10bit addressing enabled
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   from smbus3 import SMBus

   with SMBus(1) as bus:
       bus.tenbit = 1  # Enable 10bit addressing
       b = bus.read_byte_data(80, 0)
       print(b)

Example 1e: Read a byte with manually specified timeout
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Timeout can be specified in units of 10ms:

.. code:: python

   from smbus3 import SMBus

   with SMBus(1) as bus:
       bus.set_timeout(30) # Specify a timeout of 300ms
       b = bus.read_byte_data(80, 0)
       print(b)

Example 1f: Read a byte with manually specified retries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retries can be specified using ``set_retries()``:

.. code:: python

   from smbus3 import SMBus

   with SMBus(1) as bus:
       bus.set_retries(5) # Retry up to 5 times
       b = bus.read_byte_data(80, 0)
       print(b)

Example 2: Read a block of data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can read up to 32 bytes at once.

.. code:: python

   from smbus3 import SMBus

   with SMBus(1) as bus:
       # Read a block of 16 bytes from address 80, offset 0
       block = bus.read_i2c_block_data(80, 0, 16)
       # Returned value is a list of 16 bytes
       print(block)

Example 3: Write a byte
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   from smbus3 import SMBus

   with SMBus(1) as bus:
       # Write 3 bytes to address 80, offset 0:
       data = 45
       bus.write_byte_data(80, 0, data)
       data = 0x1F
       bus.write_byte_data(80, 0, data)
       data = b"\x00"
       bus.write_byte_data(80, 0, data)

Example 4: Write a block of data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to write 32 bytes at the time, but that may be
error-prone on some platforms.

Write fewer bytes and add a delay in between if you run into trouble.

.. code:: python

   from smbus3 import SMBus

   with SMBus(1) as bus:
       # Write a block of 8 bytes to address 80 from offset 0
       data = [1, 2, 3, 4, 5, 6, 7, 8]
       bus.write_i2c_block_data(80, 0, data)

   with SMBus(1) as bus:
       # Write a block of the maximum size (32 bytes) to address 80 from offset 0:
       data = [_ for _ in range(1, 32 + 1)]
       bus.write_i2c_block_data(80, 0, data)

   with SMBus(1) as bus:
       # THIS WILL FAIL WITH ValueError, AS IT EXCEEDS I2C_SMBUS_BLOCK_MAX!
       data = [_ for _ in range(1, 33 + 1)]
       bus.write_i2c_block_data(80, 0, data)

I2C
---

The smbus3 library also has support for combined read and write
transactions. ``i2c_rdwr`` is not really a SMBus feature but comes in
handy when the master needs to:

1. Read or write bulks of data larger than SMBus’ 32 bytes limit.
2. Write some data and then read from the slave with a repeated start
   and no stop bit between.

Each operation is represented by a ``i2c_msg`` message object.

Example 5: Single ``i2c_rdwr``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To perform a single read or write, simply create a message using
``i2c_msg.read()`` or ``i2c_msg.write()``, then pass the message to the
``i2c_rdwr()`` method on the bus:

.. code:: python

   from smbus3 import SMBus, i2c_msg

   with SMBus(1) as bus:
       # Read 64 bytes from address 80
       msg = i2c_msg.read(80, 64)
       bus.i2c_rdwr(msg)

       # Write a single byte to address 80
       msg = i2c_msg.write(80, [65])
       bus.i2c_rdwr(msg)

       # Write some bytes to address 80
       msg = i2c_msg.write(80, [65, 66, 67, 68])
       bus.i2c_rdwr(msg)

Example 6: Dual ``i2c_rdwr``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To perform dual operations just add more ``i2c_msg`` instances to the
bus call:

.. code:: python

   from smbus3 import SMBus, i2c_msg

   # Single transaction writing two bytes then read two at address 80
   write = i2c_msg.write(80, [40, 50])
   read = i2c_msg.read(80, 2)
   with SMBus(1) as bus:
       bus.i2c_rdwr(write, read)

Example 7: Single ``i2c_rd``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To perform a single read (combining ``i2c_msg`` creation and calling
``i2c_rdwr`` on a single message into a single method call):

.. code:: python

   from smbus3 import SMBus

   with SMBus(1) as bus:
       # Read 64 bytes from address 80
       bus.i2c_rd(80, 64)

Example 8: Single ``i2c_wr``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To perform a single write (combining ``i2c_msg`` creation and calling
``i2c_rdwr`` on a single message into a single function call):

.. code:: python

   from smbus3 import SMBus

   with SMBus(1) as bus:
       # Write a single byte to address 80
       bus.i2c_wr(80, [65])

       # Write some bytes to address 80
       bus.i2c_wr(80, [65, 66, 67, 68])

Example 9: Access ``i2c_msg`` data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All data is contained in the ``i2c_msg`` instances. Here are some data
access alternatives.

.. code:: python

   # 1: Convert message content to list
   msg = i2c_msg.write(60, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
   data = list(msg)  # data = [1, 2, 3, ...]
   print(len(data))  # => 10

   # 2: i2c_msg is iterable
   for value in msg:
       print(value)

   # 3: Through i2c_msg properties
   for k in range(msg.len):
       print(msg.buf[k])

Installation
------------

To install from PyPI, use ``pip``:

::

    pip3 install smbus3


To install from source, simply run the following command from the top of the repo:

::

    pip3 install .

Local development
-----------------

For local development, you can use the included ``Makefile`` to perform
tasks:

::

   # EG:
   make all
   # To show available commands, you can use:
   make help
   # Or alternatively bare make:
   make

Currently available targets:

-  ``all``: softclean the directory, then create the venv if it doesn’t exist, and run all common development tasks (install commit hooks, lint, format, typecheck, coverage, and then build documentation).
-  ``buildpkg``: hardclean the directory, then run pre-build tests, then build the ``.whl``
-  ``buildsdist``: build source distribution only
-  ``buildwhl``: build wheel binary distribution only
-  ``check_coverage``: check current test coverage, fails if below 90%
-  ``clean``: fully clean repo dir, including artifacts and ``.venv``
-  ``coverage``: generate coverage info on the CLI
-  ``coverage_html_report``: generate coverage info as an HTML document
-  ``coverage_xml_report``: generate coverage info as a XML document
-  ``docs``: generate the man page and HTML docs
-  ``docs_html``: generate the HTML docs
-  ``docs_man_page``: generate the man page
-  ``format``: format the code and tests with Ruff
-  ``lint``: lint the code and tests with Ruff
-  ``precommit``: install precommit hooks
-  ``softclean``: clean up artifacts without removing ``.venv``
-  ``test``: run the unit tests
-  ``testpkg``: hardclean, ``buildpkg``, then install and test with the installed version
-  ``testreleased``: install released version of the package with ``pip``, then run tests
-  ``typecheck``: run mypy typechecking on the smbus3 library
-  ``venv``: build a venv


Acknowledgements
----------------

This project is built entirely on the foundation of the
`smbus2 <https://github.com/kplindegaard/smbus2>`__ library for Python 2
& 3, written by Karl-Petter Lindegaard (@kplindegaard).
