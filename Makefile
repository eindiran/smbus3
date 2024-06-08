#==================================================================
#
#           FILE: smbus3/Makefile
#
#          USAGE: make all
#
#    DESCRIPTION: Create a virtualenv, run tests, builds docs,
#                 and other development tasks.
#
#   REQUIREMENTS: python3, venv
#
#==================================================================

# all runs clean, then creates the venv and runs tests
.PHONY: all
all: clean venv format lint test docs

# venv sets up the virtualenv
# Tracked via a touchfile
venv: .venv/touchfile

.venv/touchfile: requirements_dev.txt setup.py
	test -d .venv || python3 -m venv .venv
	. .venv/bin/activate; pip install -Ur requirements_dev.txt; pip install -U .
	touch .venv/touchfile

# Cleanup the venv and various build directories
.PHONY: clean
clean:
	rm -rf .venv
	rm -rf smbus3.egg-info
	rm -rf build
	rm -rf .ruff_cache
	rm -rf .mypy_cache

# Run the tests:
.PHONY: test
test: venv
	. .venv/bin/activate; python -m unittest tests/test_datatypes.py; python -m unittest tests/test_smbus3.py

# Build the docs:
docs: doc/_build/html/index.html

doc/_build/html/index.html: venv smbus3/smbus3.py smbus3/__init__.py doc/conf.py doc/Makefile
	. .venv/bin/activate; cd doc && make html

# Lint and format:
.PHONY: format
format: venv
	. .venv/bin/activate; ruff format .

.PHONY: lint
lint: venv format
	. .venv/bin/activate; ruff check --fix .
