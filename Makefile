PYTHON ?= .venv/bin/python
PYLINT ?= .venv/bin/pylint
PYTEST ?= .venv/bin/pytest

.PHONY: lint test check

lint:
	$(PYLINT) $$(git ls-files '*.py')

test:
	$(PYTEST) -q

check:
	$(PYTHON) -m compileall photo-import