# `fingerprint`

File fingerprint module for fast file comparison.

## Purpose

Generate file fingerprints for quick comparison. Fingerprint is a negative test: if fingerprints don't match, files are definitely different.

## Usage

```python
from fingerprint import get_fingerprint, fingerprints_match

fp = get_fingerprint("/path/to/file")
# Fingerprint(size=1234, mtime=1234567890.0, hash=None)

if fingerprints_match(fp1, fp2):
    print("Files likely identical")
```

## API Reference

### `Fingerprint`

```python
@dataclass
class Fingerprint:
    size: int       # File size in bytes
    mtime: float    # Modification time
    hash: str | None  # Content hash (optional, future)
```

### `get_fingerprint(path, include_hash=False)`

Get fingerprint for a file.

**Parameters:**
- `path` (Path): Path to file
- `include_hash` (bool): Include content hash in fingerprint

### `fingerprints_match(a, b)`

Compare two fingerprints.

**Returns:** `True` if fingerprints match (files likely identical)

## Fingerprint vs Content Hash

| Method | Speed | Accuracy |
|--------|-------|----------|
| Fingerprint (size + mtime) | Fast | High (false positives rare) |
| Content hash (SHA256) | Slow | 100% accurate |

Fingerprint is a negative test:
- **Don't match** → Files are definitely different
- **Match** → Files are likely the same (use strict mode for verification)

## Testing

```bash
python -m pytest fingerprint/tests/ -v
```
