Changelog
=========

Notable changes to `smbus3 <https://github.com/eindiran/smbus3>`__ are
recorded here.

[0.5.5] - 2024-06-28
--------------------

- Fix Twine issues with importlib-metadata (see issue `here <https://github.com/pypa/twine/issues/1125>`__).
- Enable Python3.8 support

[0.5.4] - 2024-06-14
--------------------

- Expand typing stubs with more accurate defaults
- Expanded ``Makefile`` tasks with better control over ``pip cache purge`` and ``pip uninstall smbus3``, more options for building the wheel or sdist only
- Improve packaging metadata
- Specify minimum Python version and suggest platforms
- Test vs ``smbus3`` library version matching test
- Development tooling support: create issue templates, add support for validating GitHub Actions workflows with ``action-validator`` pre-commit hook.

[0.5.3] - 2024-06-13
--------------------

- Fix broken ``setup.cfg``
- Purge ``pip`` cache on ``testreleased``

[0.5.2] - 2024-06-13
--------------------

- BROKEN DO NOT USE
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
