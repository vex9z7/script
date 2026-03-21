# TrueNAS Script Monorepo

**Platform: TrueNAS Scale (based on Debian 12)**

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
├── scriptlib/               # Shared utility namespace
│   ├── __init__.py
│   ├── dotenv/
│   ├── fingerprint/
│   ├── flockplus/
│   ├── fnmatchplus/
│   ├── log/
│   └── sync/
└── <script_name>/
    ├── __init__.py
    ├── __main__.py
    ├── app.py
    └── ...
```

## Shared Utilities

Shared utilities are reusable modules that live in the root directory. They follow a consistent structure:

```text
scriptlib/<utility-name>/
├── README.md                  # Purpose, usage, and API documentation
├── __init__.py               # Public API exports
├── <module>.py               # Implementation (optional)
└── tests/                    # Unit tests
    ├── __init__.py
    └── test_<module>.py
```

Existing utilities:
- `scriptlib.fingerprint`: File fingerprint comparison using file metadata and lazy content checks.
- `scriptlib.flockplus`: Process lock for preventing concurrent script runs.
- `scriptlib.dotenv`: Environment variable loader from `.env` files.
- `scriptlib.log`: Configurable logger with file output support.
- `scriptlib.sync`: File synchronization using fingerprint comparison.

## Script Conventions

Each script package should follow these rules:

- `__main__.py`: package entry point for internal execution and dispatch.
- `app.py`: orchestration entry point only; it should coordinate the workflow, not hold all business logic.
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

- `photo_import`: Imports photos and videos from a camera SD card on the NAS. See `photo_import/README.md`.

Operational entrypoint:
- Use `python3 /path/to/repo/run.py <script_name>` from cron or other schedulers.
- Current script names: `photo_import`

### System Dependencies

Each script must explicitly list its external system tool dependencies. These are standard Linux/TrueNAS tools assumed to be present on the system.

**photo-import:**
| Tool | Purpose | Source |
|------|---------|--------|
| `lsblk` | List block devices | util-linux (core) |
| `mount` | Mount storage devices | util-linux (core) |
| `umount` | Unmount storage devices | util-linux (core) |
| `mountpoint` | Check if path is mount point | util-linux (core) |

## Development Approach

This repository is meant for maintainable automation, not throwaway one-file scripts.

Before adding behavior:
1. Write or update the script-level README.
2. Keep configuration explicit and local.
3. Prefer deterministic behavior over convenience.
4. Handle failure paths carefully, especially around mounts and unmounts.

## Development Tooling

The repo uses `pylint` for linting and `pytest` for testing.
The repo is pinned to Python `3.11.9` via [.python-version](/home/dev/git/script/.python-version).

Setup:
```bash
python3 -m venv .venv --upgrade
.venv/bin/pip install -r requirements-dev.txt
```

Common commands (via Makefile):
- `make lint`
- `make test`

Or directly:
- `pylint $(git ls-files '*.py')`
- `pytest -q`

## Status

`photo-import` is the first structured script in the monorepo. Additional automations should follow the same shape.
