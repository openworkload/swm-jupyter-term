PYTHON=python3.10
VENV_BIN=.venv/bin

RUNTEST=$(PYTHON) -m unittest -v -b
ALLMODULES=$(patsubst %.py, %.py, $(wildcard test*.py))

.PHONY: prepare-venv
.ONESHELL:
prepare-venv: .SHELLFLAGS := -euo pipefail -c
prepare-venv: SHELL := bash
prepare-venv:
	$(PYTHON) -m venv --system-site-packages .venv
	$(VENV_BIN)/pip install --ignore-installed --no-deps -r requirements.txt

.PHONY: run
run:
	. .venv/bin/activate
	jupyterhub --debug

.PHONY: format
format:
	. .venv/bin/activate
	$(VENV_BIN)/autoflake -i -r --ignore-init-module-imports swmjupyter
	$(VENV_BIN)/black swmjupyter
	$(VENV_BIN)/isort swmjupyter

.PHONY: check
check:
	. .venv/bin/activate
	$(VENV_BIN)/ruff check swmjupyter
	$(VENV_BIN)/mypy swmjupyter
	$(VENV_BIN)/bandit -r swmjupyter -c "pyproject.toml" --silent

.PHONY: package
package:
	. .venv/bin/activate
	$(PYTHON) -m build

.PHONY: clean
clean:
	rm -fr ./dist
	rm -fr swmjupyter.egg-info
	rm -fr build

.PHONY: upload
upload:
	. .venv/bin/activate
	$(PYTHON) -m twine upload --verbose --config-file .pypirc dist/*

.PHONY: test
test:
	${RUNTEST} ${ALLMODULES}

% : test%.py
	${RUNTEST} test$@

.PHONY: update-client-package
update-client-package:
	. .venv/bin/activate
	pip install --upgrade -e ../swm-python-client

.PHONY: requirements
requirements: requirements.txt
	make prepare-venv || true

requirements.txt: requirements.in
	@pip-compile $<
