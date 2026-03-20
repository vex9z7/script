# `lock`

A file-based process lock utility using Python's native `fcntl` module. Linux only, no external dependencies.

## Purpose

Prevents multiple instances of a script from running simultaneously. When a script attempts to start while another instance is active, it raises `LockError`.

## Layout

```text
lock/
├── __init__.py
├── file_lock.py
├── tests/
│   └── test_file_lock.py
└── README.md
```

## Usage

### Context Manager (Recommended)

```python
from lock import ProcessLock

with ProcessLock("/var/run/my-script.lock"):
    # Lock is held for this block
    pass
# Lock is automatically released
```

### ensure_locked

```python
from lock import ensure_locked

ensure_locked("/var/run/my-script.lock")
# Exits with error if another instance is running
```

## API Reference

### `ProcessLock(lock_path)`

Creates a new lock instance for the given path.

**Parameters:**
- `lock_path`: Path to the lock file

**Methods:**
- `acquire()`: Acquire the lock. Raises `LockError` if already locked.
- `release()`: Release the lock.
- `is_locked()`: Check if the lock is currently held by a running process.

**Context Manager:** Supports `with` statement for automatic cleanup.

### `ensure_locked(lock_path)`

Acquire lock or exit with error.

**Behavior:**
- If lock is free: acquires it and returns the lock object
- If lock is held by another process: prints error to stderr and calls `sys.exit(1)`

### `LockError`

Exception raised when lock acquisition fails (e.g., another process holds the lock).

## Features

- Linux only (uses `fcntl`)
- No external dependencies
- Process-aware: checks if the PID in the lock file is still running
- Atomic file locking: uses `LOCK_NB` (non-blocking)
- Nested lock prevention
- Automatic cleanup via context manager
- PID tracking in lock file

## Lock File Location

- `/var/run/<script-name>.lock` (requires root)
- `/tmp/<script-name>.lock` (user-accessible)

## Testing

```bash
python -m pytest lock/tests/ -v
```
