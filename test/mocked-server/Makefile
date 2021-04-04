.PHONY: prepare
.ONESHELL:
prepare: .SHELLFLAGS := -euo pipefail -c
prepare: SHELL := bash
prepare:
	python3 -m pip install 'virtualenv>=16.4.3'
	virtualenv --system-site-packages .venv
	.venv/bin/pip install --ignore-installed --no-deps -r requirements.txt
	. .venv/bin/activate
	python3 setup.py install --user

.PHONY: requirements
requirements: requirements.txt
	make prepare || true

requirements.txt: requirements.in
	. .venv/bin/activate
	@pip-compile $<
