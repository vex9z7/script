# `flockplus`

A simple file-based process lock using Python's native `fcntl.flock()`. Linux only, no external dependencies.

## Usage

```python
from flockplus import ProcessLock

with ProcessLock("/tmp/my-script.lock"):
    # work
```

## API

### `ProcessLock(lock_path)`

Context manager that acquires an exclusive lock using `fcntl.flock()`.

- Raises `OSError` if lock is held or permission denied
- Lock is automatically released on exit

## Testing

```bash
python -m pytest flockplus/tests/ -v
```
