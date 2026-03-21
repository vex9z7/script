# `pyrsync`

Thin Python wrapper around the system `rsync` command.

## Purpose

Provide repository-local sync helpers while delegating the actual directory convergence work to `rsync`.

## Responsibilities

- build an `rsync` command for local directory sync
- apply caller-provided filter rules
- preserve recursive structure and modification times
- expose a small structured result for copied and deleted entries

## Notes

- `pyrsync` depends on the system `rsync` binary being available.
- Logging remains the responsibility of the calling script, not this wrapper.
