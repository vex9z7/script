# `fingerprint`

File fingerprint module for fast file/directory comparison.

## Purpose

Generate fingerprints for files and directories, providing fast comparison methods. A fingerprint is a **negative test**: if fingerprints don't match, the targets are definitely different; if they match, they are likely identical within this module's comparison rules.

## Responsibilities

- Calculate and store file metadata (size, mtime, ctime)
- Compute content hash (lazy, on demand)
- Compare two fingerprints for identity

## What fingerprint IS

- A **fast approximation** of file identity
- A **negative test**: mismatched fingerprints prove files are different
- Composed of observable attributes: size, mtime, ctime, hash

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
    ctime: float                       # Metadata change time (from stat)
    get_sha256: Callable[[], str]      # Lazy content hash (None for directories)
```

### `get_fingerprint(path: Path) -> Fingerprint`

Generate fingerprint for a file or directory.

### `fingerprints_match(a: Fingerprint, b: Fingerprint) -> bool`

Compare two fingerprints:

1. If `mtime` differs → return `False` immediately (no hash computed)
2. If `ctime` differs → return `False` immediately
3. If `size` differs → return `False`
4. Compute and compare `sha256` hashes

`ctime` is part of the intended comparison contract. If two files have identical content but different `ctime`, `fingerprints_match()` returns `False` and downstream consumers may treat the file as changed.

**Performance note:** Hash computation is lazy and skipped when mtime/ctime/size differ.

## Comparison Properties

| Scenario | `fingerprints_match` result |
|----------|----------------------------|
| `mtime` differs | `False` (proved) |
| `ctime` differs | `False` (proved by policy) |
| `size` differs | `False` (proved) |
| Both equal, content differs | `False` (proved via hash) |
| All equal | `True` (likely) |

## Testing Guidance

- Tests that exercise fingerprint equality should not rely on the host filesystem accidentally producing matching timestamps.
- When the expected result depends on exact fingerprint fields, construct `Fingerprint` instances directly or mock fingerprint creation.
- Integration tests may still use real files, but should not assume `ctime` stability across platforms.

## TODO

- Directory fingerprints are currently shallow metadata-based approximations. They may miss cases where child file contents change without a corresponding directory-level metadata change.

## Testing

```bash
python -m pytest fingerprint/tests/ -v
```
