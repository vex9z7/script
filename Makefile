PYTHON ?= .venv/bin/python
RUFF ?= .venv/bin/ruff

.PHONY: fmt lint check

fmt:
	$(RUFF) format .

lint:
	$(RUFF) check .

check:
	$(PYTHON) -m compileall photo-import
