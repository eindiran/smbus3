Changelog
=========

Notable changes to `smbus3 <https://github.com/eindiran/smbus3>`__ are
recorded here.

[0.5.2] - 2024-06-13
--------------------

- Switch to using ``setup.cfg`` for configuration metadata.
- Ensure packages are generated without ``bdist_wheel`` option ``universal``, as Python 2 and Windows aren't supported.
- Add testing option in Makefile for using the PyPI package
- Update documentation with current Makefile tasks

[0.5.1] - 2024-06-13
--------------------

- Documentation updates.
- Remove MANIFEST.in

[0.5.0] - 2024-06-13
--------------------

- Initial version of ``smbus3`` published.
-  Split from `smbus2 <https://github.com/kplindegaard/smbus2>`__ and
   refactor.
- Remove Python 2 support and no longer list pre-3.9 Python 3s.
- Add automated local dev tooling.
- Reach 100% coverage in unit tests.
- Add support for 10bit addressing.
- Add support for setting retry count manually.
- Add support for setting timeout manually.
- Update type stubs.
