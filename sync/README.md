# `sync`

File synchronization utility for making destination match source.

## Purpose

Synchronize files from source to destination directory. Decides what to copy, skip, or delete based on fingerprint comparison.

## Responsibilities

- Traverse source directory with optional filtering
- Compare source files with destination files using fingerprints
- Copy new/modified files to destination
- Delete extra files in destination not present in source
- Delegate fingerprint comparison to `fingerprint` module

## What sync IS

- A **file operation** tool (copy, skip, delete)
- Uses fingerprints for comparison decisions
- A **consumer** of fingerprint module

## What sync IS NOT

- A fingerprint calculator (delegates to `fingerprint` module)
- A guarantee of bit-perfect sync (uses fingerprint as approximation)
- Responsible for deciding what "match" means (that is fingerprint's job)

## Architecture

```
sync
  └── uses ──► fingerprint
                    ├── get_fingerprint()     # Calculate fingerprint
                    └── fingerprints_match()  # Compare fingerprints
```

**Separation of concerns:**
- `fingerprint`: "Are these two files likely the same?" (yes/no)
- `sync`: "Based on that answer, what should I do?" (copy/skip/delete)

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

### `sync(source, destination, filter=None, strict=False) -> SyncStats`

**Parameters:**
- `source` (Path): Source directory to sync from
- `destination` (Path): Destination directory to sync to
- `filter` (Callable[[Path], bool] | None): Filter function for files/directories
- `strict` (bool): When True, verify content matches when fingerprint matches

**Returns:** `SyncStats` with `copied`, `skipped`, `deleted` counts

### `SyncStats`

```python
@dataclass
class SyncStats:
    copied: int   # Files copied to destination
    skipped: int # Files skipped (fingerprint matched)
    deleted: int # Extra files deleted in destination
```

## Behavior

1. Walk source directory, apply filter if provided
2. For each source file:
   - If destination doesn't exist → copy
   - If fingerprint matches → skip (non-strict) or verify content (strict)
   - If fingerprint differs → copy
3. After sync, delete files in destination not present in source

## Filter Callback

The filter receives full paths for both files and directories:

```python
def my_filter(path: Path) -> bool:
    if path.is_dir():
        return path.name.lower() != "thumbnails"  # Skip thumbnails folder
    return path.suffix.lower() in {".jpg", ".mp4"}  # Only photos/videos

sync(source, dest, filter=my_filter)
```

## Strict Mode

| Mode | Fingerprint matches | Action |
|------|---------------------|--------|
| Non-strict | Yes | Skip (trust fingerprint) |
| Non-strict | No | Copy |
| Strict | Yes | Verify content (hash), skip if identical |
| Strict | No | Copy |

## Testing

```bash
python -m pytest sync/tests/ -v
```
