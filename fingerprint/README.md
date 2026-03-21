# `fingerprint`

File fingerprint module for fast file/directory comparison.

## Purpose

Generate fingerprints for files and directories, providing fast comparison methods. A fingerprint is a **negative test**: if fingerprints don't match, the targets are definitely different; if they match, they are likely identical.

## Responsibilities

- Calculate and store file metadata (size, mtime)
- Compute content hash (lazy, on demand)
- Compare two fingerprints for identity

## What fingerprint IS

- A **fast approximation** of file identity
- A **negative test**: mismatched fingerprints prove files are different
- Composed of observable attributes: size, mtime, hash

## What fingerprint IS NOT

- A guarantee of identity (use strict mode for verification)
- A sync mechanism
- A file operation tool

## Usage

```python
from fingerprint import get_fingerprint, fingerprints_match

fp = get_fingerprint("/path/to/file")

# Compare two fingerprints
if fingerprints_match(fp1, fp2):
    print("Fingerprints match - files likely identical")
else:
    print("Fingerprints differ - files are definitely different")
```

## API Reference

### `Fingerprint`

```python
@dataclass
class Fingerprint:
    size: int                          # File size in bytes (0 for directories)
    mtime: float                       # Modification time (from stat)
    get_sha256: Callable[[], str]      # Lazy content hash (None for directories)
```

### `get_fingerprint(path: Path) -> Fingerprint`

Generate fingerprint for a file or directory.

### `fingerprints_match(a: Fingerprint, b: Fingerprint) -> bool`

Compare two fingerprints:

1. If `mtime` differs → return `False` immediately (no hash computed)
2. If `size` differs → return `False`
3. Compute and compare `sha256` hashes

**Performance note:** Hash computation is lazy and skipped when mtime/size differ.

## Comparison Properties

| Scenario | `fingerprints_match` result |
|----------|----------------------------|
| `mtime` differs | `False` (proved) |
| `size` differs | `False` (proved) |
| Both equal, content differs | `False` (proved via hash) |
| All equal | `True` (likely) |

## Testing

```bash
python -m pytest fingerprint/tests/ -v
```
