#==================================================================
#
#           FILE: smbus3/Makefile
#
#          USAGE: make all
#
#    DESCRIPTION: Create a virtualenv, run tests, builds docs,
#                 and other development tasks.
#
#   REQUIREMENTS: python3, pip, venv
#
#==================================================================

# Help to list makefile targets:
# This is first so that it will be the default target.
.PHONY: help
help: Makefile
	@echo "Available targets:"
	@echo "==================="
	@LC_ALL=C $(MAKE) -pRrq -f $(firstword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/(^|\n)# Files(\n|$$)/,/(^|\n)# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$@$$' | grep -E -v -e "_build"

# all runs softclean, then creates the venv and runs tests
.PHONY: all
all: softclean venv precommit format lint test typecheck coverage coverage_html_report docs

# venv sets up the virtualenv
# Tracked via a touchfile
venv: .venv/touchfile

.venv/touchfile: requirements_dev.txt setup.py
	@echo "\n\033[0;32mSetting up venv\033[0m\n"
	test -d .venv || python3 -m venv .venv
	. .venv/bin/activate; pip install -r requirements_dev.txt; pip install .
	touch .venv/touchfile
	@echo "\n\033[0;32mvenv complete\033[0m\n"

# Cleanup artifacts without changing venv
.PHONY: softclean
softclean:
	rm -rf smbus3.egg-info
	rm -rf dist
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

# Cleanup the venv and various build directories
.PHONY: clean
clean: softclean
	rm -rf .venv

# Run the tests:
.PHONY: test
test: venv
	@echo "\n\033[0;32mRunning smbus3 unittest suite\033[0m\n"
	. .venv/bin/activate; coverage run -m unittest tests
	@echo "\n\033[0;32msmbus3 unittest suite complete\033[0m\n"

# Typecheck the stub files with mypy
.PHONY: typecheck
typecheck: venv
	@echo "\n\033[0;32mTypechecking with mypy\033[0m\n"
	. .venv/bin/activate; mypy . --exclude "build/"
	@echo "\n\033[0;32mTypechecking complete\033[0m\n"

.PHONY: coverage
coverage: test
	@echo "\n\033[0;32mGenerating CLI coverage report\033[0m\n"
	. .venv/bin/activate; coverage report -m

.PHONY: coverage_html_report
coverage_html_report: test
	@echo "\n\033[0;32mGenerating HTML coverage report\033[0m\n"
	. .venv/bin/activate; coverage html

.PHONY: coverage_xml_report
coverage_xml_report: test
	@echo "\n\033[0;32mGenerating XML coverage report\033[0m\n"
	. .venv/bin/activate; coverage xml

.PHONY: _echo_coverage_total
_echo_coverage_total:
	@. .venv/bin/activate; coverage json --quiet; python -c "import json; f = open('coverage.json'); s = f.read(); x = json.loads(s); print(x['totals']['percent_covered_display']); f.close()"
	@rm -rf coverage.json

.PHONY: check_coverage
check_coverage: test
	@if (( $$(make _echo_coverage_total) < 90 )); then exit 1; else echo "Coverage percentage >=90"; fi

# Build the docs:
docs: docs_html docs_man_page
	@echo "\n\033[0;32mBuilding documentation complete!\033[0m\n"

docs_html: doc/_build/html/index.html

docs_man_page: doc/_build/man/smbus3.1

doc/_build/html/index.html: venv smbus3/smbus3.py smbus3/__init__.py doc/conf.py doc/Makefile
	@echo "\n\033[0;32mBuilding Sphinx HTML docs\033[0m\n"
	. .venv/bin/activate; cd doc && make html
	@echo "\n\033[0;32mHTML docs complete\033[0m\n"

doc/_build/man/smbus3.1: venv smbus3/smbus3.py smbus3/__init__.py doc/conf.py doc/Makefile
	@echo "\n\033[0;32mBuilding manpage\033[0m\n"
	. .venv/bin/activate; cd doc && make man
	@echo "\n\033[0;32mManpage complete\033[0m\n"

# Setup pre-commit
precommit: .venv/pre-commit-touchfile

.venv/pre-commit-touchfile: .pre-commit-config.yaml
	@echo "\n\033[0;32mInstalling precommit hooks\033[0m\n"
	. .venv/bin/activate; pre-commit install
	touch .venv/pre-commit-touchfile
	@echo "\n\033[0;32mPrecommit hooks installed successfully!\033[0m\n"

# Lint and format:
.PHONY: format
format: venv .ruff.toml
	@echo "\n\033[0;32mRunning formatter\033[0m\n"
	. .venv/bin/activate; ruff format .
	@echo "\n\033[0;32mFormatting complete!\033[0m\n"

.PHONY: lint
lint: venv format .ruff.toml
	@echo "\n\033[0;32mRunning linter\033[0m\n"
	. .venv/bin/activate; ruff check --fix .
	@echo "\n\033[0;32mLinting complete!\033[0m\n"

# Build the package:
.PHONY: buildpkg
buildpkg: clean venv precommit format lint test typecheck check_coverage
	@echo "\n\033[0;32mBuilding source distribution\033[0m\n"
	. .venv/bin/activate; python setup.py sdist
	@echo "\n\033[0;32mBuilding universal .whl\033[0m\n"
	. .venv/bin/activate; python setup.py bdist_wheel --universal
	@echo "\n\033[0;32mBuild complete!\033[0m\n"

# Test built package
.PHONY: testpkg
testpkg: buildpkg
	@echo "\n\033[0;32mInstalling built .whl\033[0m\n"
	. .venv/bin/activate; pip uninstall --yes smbus3; pip install dist/smbus3-*.whl
	@echo "\n\033[0;32mRunning tests with installed .whl\033[0m\n"
	make test
	@echo "\n\033[0;32mSuccess! Tests with .whl passed!\033[0m\n"
