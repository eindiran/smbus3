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

# Help to list makefile targets:
# This is first so that it will be the default target.
.PHONY: help
help: Makefile
	@echo "Available targets:"
	@echo "==================="
	@LC_ALL=C $(MAKE) -pRrq -f $(firstword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/(^|\n)# Files(\n|$$)/,/(^|\n)# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$@$$' | grep -E -v -e "_build"

# all runs clean, then creates the venv and runs tests
.PHONY: all
all: clean venv precommit format lint test coverage coverage_html_report docs

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
	rm -rf doc/_build
	rm -rf doc/doctrees
	rm -rf doc/man
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf htmlcov
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

# Run the tests:
.PHONY: test
test: venv
	. .venv/bin/activate; coverage run -m unittest tests/test_datatypes.py; coverage run -m unittest tests/test_smbus3.py

.PHONY: coverage
coverage: test
	. .venv/bin/activate; coverage report -m

.PHONY: coverage_html_report
coverage_html_report: test
	. .venv/bin/activate; coverage html

# Build the docs:
docs: docs_html docs_man_page

docs_html: doc/_build/html/index.html

docs_man_page: doc/_build/man/smbus3.1

doc/_build/html/index.html: venv smbus3/smbus3.py smbus3/__init__.py doc/conf.py doc/Makefile
	. .venv/bin/activate; cd doc && make html

doc/_build/man/smbus3.1: venv smbus3/smbus3.py smbus3/__init__.py doc/conf.py doc/Makefile
	. .venv/bin/activate; cd doc && make man

# Setup pre-commit
precommit: .venv/pre-commit-touchfile

.venv/pre-commit-touchfile: .pre-commit-config.yaml
	. .venv/bin/activate; pre-commit install
	touch .venv/pre-commit-touchfile

# Lint and format:
.PHONY: format
format: venv .ruff.toml
	. .venv/bin/activate; ruff format .

.PHONY: lint
lint: venv format .ruff.toml
	. .venv/bin/activate; ruff check --fix .
