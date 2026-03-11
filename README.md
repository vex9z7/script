# TrueNAS Script Monorepo

This repository is a monorepo for small operational scripts that run on a TrueNAS system.

The design constraints are intentional:
- Each automation lives in its own directory.
- Scripts should prefer Python over shell when the logic is non-trivial.
- Scripts must avoid external dependencies. Use only the Python standard library or POSIX/TrueNAS system tools.
- Each script should be runnable independently and documented locally.

## Repository Layout

The repository is organized by automation task:

```text
.
├── README.md
├── LICENSE
└── photo-import/
    ├── README.md
    ├── main.py
    ├── config.py
    ├── detect.py
    ├── mount.py
    ├── photo_copy.py
    ├── cleanup.py
    └── logging_utils.py
```

The repository should grow by adding more script directories at the top level.

## Script Conventions

Each script directory should follow these rules:

- `README.md`: purpose, configuration, execution model, and operational notes.
- `main.py`: entry point only; it should orchestrate the workflow, not hold all business logic.
- Package modules: implementation split by responsibility.
- `config.py`: all user-editable settings in one place.

Preferred Python module responsibilities:
- `detect`: discover devices or inputs.
- `mount`: mount and unmount storage.
- `photo_copy`: file-selection and copy logic.
- `cleanup`: teardown, state cleanup, and error-safe finalization.
- `logging_utils`: simple local logging helpers.

Shell scripts are acceptable when the task is truly simple, but Python is the default.

## Current Script: `photo-import`

`photo-import` is intended to automate ingesting photos and videos from a camera SD card inserted into the NAS.

Target workflow:
1. Detect an inserted SD card.
2. Mount it read-only at a configured mount point.
3. Copy image and video files to a configured destination.
4. Skip thumbnails and other preview artifacts.
5. Unmount the SD card automatically.
6. Exit cleanly when no suitable card is present.

Configurable inputs for `photo-import`:
- Destination path
- Temporary mount path
- Allowed file extensions
- Thumbnail exclusion rules
- Logging and state paths

## Development Approach

This repository is meant for maintainable automation, not throwaway one-file scripts.

Before adding behavior:
1. Write or update the script-level README.
2. Keep configuration explicit and local.
3. Prefer deterministic behavior over convenience.
4. Handle failure paths carefully, especially around mounts and unmounts.

## Development Tooling

The repo includes `ruff` configuration in [`pyproject.toml`](/home/dev/git/script/pyproject.toml) for both formatting and linting.

Common commands:
- `make fmt`
- `make lint`
- `make check`

Recommended setup:
- `python -m venv .venv`
- `.venv/bin/pip install -r requirements-dev.txt`

The `Makefile` uses `.venv/bin/python` and `.venv/bin/ruff` by default, so activation is optional.

## Status

`photo-import` is now the first structured script in the monorepo. Additional automations should follow the same shape.
