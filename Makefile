PYTHON ?= .venv/bin/python
RUFF ?= .venv/bin/ruff
PYTEST ?= .venv/bin/pytest

.PHONY: fmt lint test check

fmt:
	$(RUFF) format .

lint:
	$(RUFF) check .

test:
	$(PYTEST) -q photo-import/tests

check:
	$(PYTHON) -m compileall photo-import
