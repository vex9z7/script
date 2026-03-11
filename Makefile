PYTHON ?= python
RUFF ?= ruff

.PHONY: fmt lint check

fmt:
	$(RUFF) format .

lint:
	$(RUFF) check .

check:
	$(PYTHON) -m compileall photo-import
