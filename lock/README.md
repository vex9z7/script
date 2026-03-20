# `lock`

A cross-platform file-based process lock utility using Python's native `fcntl` (Unix) and `msvcrt` (Windows) modules. No external dependencies required.

## Purpose

Prevents multiple instances of a script from running simultaneously. When a script attempts to start while another instance is active, it detects the existing lock and exits with an error message.

## Layout

```text
lock/
├── __init__.py
├── _native.py
├── file_lock.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_file_lock.py
└── README.md
```

## Usage

### Basic Usage (Recommended)

```python
from lock import ensure_locked

lock = ensure_locked("/var/run/my-script.lock")
# Script continues if lock acquired successfully
# Otherwise prints error and exits

# ... do work ...

lock.release()
```

### Context Manager

```python
from lock import ProcessLock

lock_path = "/var/run/my-script.lock"
with ProcessLock(lock_path) as lock:
    # Lock is held for this block
    pass
# Lock is automatically released
```

### Manual Acquisition

```python
from lock import acquire_lock

lock = acquire_lock("/var/run/my-script.lock")
# Lock acquired, proceed with work
lock.release()
```

### Checking Lock Status

```python
from lock import ProcessLock

lock = ProcessLock("/var/run/my-script.lock")
if lock.is_locked():
    print("Another instance is running")
else:
    print("No other instance running")
```

## API Reference

### `ProcessLock(lock_path)`

Creates a new lock instance for the given path.

**Parameters:**
- `lock_path` (str): Path to the lock file

**Methods:**
- `acquire()`: Acquire the lock. Raises `LockFailedError` if already locked.
- `release()`: Release the lock.
- `is_locked()`: Check if the lock is currently held by a running process.

**Context Manager:** Supports `with` statement for automatic cleanup.

### `ensure_locked(lock_path)`

Acquire lock or exit with error. This is the simplest way to add locking to a script.

**Parameters:**
- `lock_path` (str): Path to the lock file

**Behavior:**
- If lock is free: acquires it and returns the lock object
- If lock is held by another process: prints error to stderr and calls `sys.exit(1)`

### `acquire_lock(lock_path)`

Acquire lock without checking if already locked.

**Parameters:**
- `lock_path` (str): Path to the lock file

**Returns:** `ProcessLock` instance

### `is_process_running(pid)`

Check if a process with the given PID is running.

**Parameters:**
- `pid` (int): Process ID to check

**Returns:** `bool`

### `LockFailedError`

Exception raised when lock acquisition fails.

## Features

- Cross-platform: works on Unix (via `fcntl`) and Windows (via `msvcrt`)
- No external dependencies: uses only Python standard library
- Process-aware: checks if the PID in the lock file is still running
- Atomic file locking: uses `LOCK_NB` (non-blocking) for immediate acquisition
- Nested lock prevention: same `ProcessLock` instance cannot acquire twice
- Automatic cleanup: context manager ensures lock release
- PID tracking: lock file contains the PID for debugging

## Lock File Location

Lock files are created at the specified path. For system-wide scripts, common locations:
- `/var/run/<script-name>.lock` (requires root)
- `/tmp/<script-name>.lock` (user-accessible)

## Example: Adding Locking to a Script

```python
#!/usr/bin/env python
import sys
from lock import ensure_locked

def main():
    lock = ensure_locked("/var/run/photo-import.lock")
    
    try:
        # Your script logic here
        print("Script running...")
    finally:
        lock.release()

if __name__ == "__main__":
    main()
```

## Testing

```bash
python -m pytest lock/tests/ -v
```
