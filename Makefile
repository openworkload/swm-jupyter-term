PYTHON=python3.10
VENV_BIN=.venv/bin

RUNTEST=$(PYTHON) -m unittest -v -b
ALLMODULES=$(patsubst %.py, %.py, $(wildcard test*.py))

.PHONY: prepare-venv
.ONESHELL:
prepare-venv: .SHELLFLAGS := -euo pipefail -c
prepare-venv: SHELL := bash
prepare-venv:
	virtualenv --system-site-packages .venv
	$(VENV_BIN)/pip install --ignore-installed --no-deps -r requirements.txt

.PHONY: format
format:
	. .venv/bin/activate
	$(VENV_BIN)/autoflake -i -r --ignore-init-module-imports swm_jupyter_spawner
	$(VENV_BIN)/black swm_jupyter_spawner
	$(VENV_BIN)/isort swm_jupyter_spawner

.PHONY: check
check:
	. .venv/bin/activate
	$(VENV_BIN)/ruff check swm_jupyter_spawner
	$(VENV_BIN)/mypy swm_jupyter_spawner
	$(VENV_BIN)/bandit -r swm_jupyter_spawner -c "pyproject.toml" --silent

.PHONY: package
package:
	. .venv/bin/activate
	$(PYTHON) setup.py bdist_wheel

.PHONY: clean
clean:
	rm -f ./dist/*.whl

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
