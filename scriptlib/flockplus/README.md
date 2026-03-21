# `flockplus`

A simple file-based lock using Python's native `fcntl.flock()`. Linux only, no external dependencies.

## Usage

```python
from scriptlib.flockplus import FileLock

with FileLock("/tmp/my-script.lock"):
    # work
```

## API

### `FileLock(lock_path)`

Context manager that acquires an exclusive lock using `fcntl.flock()`.

- Raises `OSError` if lock is held or permission denied
- Lock is automatically released on exit

## Testing

```bash
python -m pytest flockplus/tests/ -v
```
