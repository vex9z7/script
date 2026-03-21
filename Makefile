PYTHON ?= .venv/bin/python
PYLINT ?= .venv/bin/pylint
PYTEST ?= .venv/bin/pytest

.PHONY: lint test check

lint:
	$(PYLINT) $$(rg --files -g '*.py' -g '!.venv/**')

test:
	$(PYTEST) -q

check:
	$(PYTHON) -m compileall photo_import scriptlib
