# TrueNAS Script Monorepo

**Platform: Linux only**

This repository is a monorepo for small operational scripts that run on a TrueNAS system.

The design constraints are intentional:
- Each automation lives in its own directory.
- Scripts should prefer Python over shell when the logic is non-trivial.
- Scripts must avoid external dependencies. Use only the Python standard library or POSIX/TrueNAS system tools.
- Each script should be runnable independently and documented locally.

## Repository Layout

Each script or shared utility must live in its own top-level directory. This is a strict rule.

```text
.
├── README.md
├── LICENSE
├── fingerprint/              # Shared utility
│   ├── __init__.py
│   └── tests/
├── lock/                    # Shared utility
│   ├── README.md
│   ├── __init__.py
│   ├── file_lock.py
│   └── tests/
├── dotenv/                  # Shared utility
│   ├── __init__.py
│   └── tests/
├── log/                     # Shared utility
│   ├── __init__.py
│   └── tests/
├── sync/                    # Shared utility
│   ├── __init__.py
│   └── tests/
└── <script-name>/
    ├── README.md
    ├── main.py
    └── ...
```

## Shared Utilities

Shared utilities are reusable modules that live in the root directory. They follow a consistent structure:

```text
<utility-name>/
├── README.md                  # Purpose, usage, and API documentation
├── __init__.py               # Public API exports
├── <module>.py               # Implementation (optional)
└── tests/                    # Unit tests
    ├── __init__.py
    └── test_<module>.py
```

Existing utilities:
- `fingerprint`: File fingerprint comparison using size and mtime.
- `lock`: Process lock for preventing concurrent script runs.
- `dotenv`: Environment variable loader from `.env` files.
- `log`: Configurable logger with file output support.
- `sync`: File synchronization using fingerprint comparison.

## Script Conventions

Each script directory should follow these rules:

- `main.py`: entry point only; it should orchestrate the workflow, not hold all business logic. Must include `#!/usr/bin/env python3` shebang.
- `config.py`: all user-editable settings in one place. Support environment variables for configuration.
- `README.md`: purpose, configuration, execution model, and operational notes.
- Package modules: implementation split by responsibility.
- `.env.example`: example environment variables for configuration.

Preferred Python module responsibilities:
- `detect`: discover devices or inputs.
- `mount`: mount and unmount storage.
- `cleanup`: teardown, state cleanup, and error-safe finalization.

Shell scripts are acceptable when the task is truly simple, but Python is the default.

**Do not duplicate shared utilities.** If a module with similar functionality exists (e.g., `sync`, `fingerprint`, `lock`, `dotenv`, `log`), use it instead of creating a new implementation. Duplication is not tolerated.

## Scripts

- `photo-import`: Imports photos and videos from a camera SD card on the NAS. See [photo-import/README.md](/home/dev/git/script/photo-import/README.md).

## Development Approach

This repository is meant for maintainable automation, not throwaway one-file scripts.

Before adding behavior:
1. Write or update the script-level README.
2. Keep configuration explicit and local.
3. Prefer deterministic behavior over convenience.
4. Handle failure paths carefully, especially around mounts and unmounts.

## Development Tooling

The repo includes `ruff` configuration in [`pyproject.toml`](/home/dev/git/script/pyproject.toml) for both formatting and linting.
The repo is pinned to Python `3.11.9` via [.python-version](/home/dev/git/script/.python-version).

Common commands:
- `make fmt`
- `make lint`
- `make check`

Recommended setup:
- `python -m venv .venv`
- `.venv/bin/pip install -r requirements-dev.txt`

The `Makefile` uses `.venv/bin/python` and `.venv/bin/ruff` by default, so activation is optional.

## Status

`photo-import` is the first structured script in the monorepo. Additional automations should follow the same shape.
