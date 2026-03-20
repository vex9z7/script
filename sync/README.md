# `sync`

File synchronization utility that makes destination match source based on fingerprint comparison.

## Purpose

Synchronize files from a source directory to a destination directory. Supports filtering and strict mode for content verification.

## Usage

```python
from sync import sync

stats = sync(
    source="/path/to/source",
    destination="/path/to/dest",
    filter=lambda p: p.is_dir() or p.suffix.lower() in {".jpg", ".mp4"},
)
print(f"Copied: {stats.copied}, Skipped: {stats.skipped}, Deleted: {stats.deleted}")
```

## API Reference

### `sync(source, destination, filter=None, strict=False)`

**Parameters:**
- `source` (Path): Source directory to sync from
- `destination` (Path): Destination directory to sync to
- `filter` (Callable[[Path], bool]): Filter function, receives full path for both files and directories. Return True to include.
- `strict` (bool): When True, verify file content matches even when fingerprint matches

**Returns:** `SyncStats` with `copied`, `skipped`, `deleted` counts

## Filter Callback

The filter receives full paths for both files and directories:

```python
def my_filter(path: Path) -> bool:
    if path.is_dir():
        return path.name.lower() != "thumbnails"  # Filter directories
    return path.suffix.lower() in {".jpg", ".mp4"}  # Filter files

sync(source, dest, filter=my_filter)
```

## Behavior

1. Copy new files from source to destination
2. Skip files where fingerprint matches (size + mtime)
3. In strict mode: verify content matches when fingerprint matches
4. Delete extra files in destination not present in source

## Fingerprint

Fingerprint comparison is a fast negative test:
- If fingerprints **don't match** → files are different (proven)
- If fingerprints **match** → files are likely the same

Strict mode adds content verification for 100% accuracy when fingerprints match.

## Testing

```bash
python -m pytest sync/tests/ -v
```
