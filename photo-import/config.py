from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import dotenv

dotenv.load_dotenv()

_THIS_DIR = Path(__file__).parent


def _load_patterns(path: Path) -> list[tuple[str, bool]]:
    """Load fnmatch patterns from a file.

    Returns list of (pattern, excluded) tuples.
    - Lines starting with '!' are exclude patterns (excluded=True)
    - Other lines are include patterns (excluded=False)
    - Comments (#) are ignored
    """
    patterns: list[tuple[str, bool]] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("!"):
                patterns.append((line[1:], True))
            else:
                patterns.append((line, False))
    return patterns


_IGNORE_PATTERNS = _load_patterns(_THIS_DIR / ".photoignore")
_DEVICE_PATTERNS = _load_patterns(_THIS_DIR / ".deviceignore")


@dataclass(frozen=True)
class Config:
    log_file: Path | None = (
        Path(os.environ["PHOTO_IMPORT_LOG_FILE"])
        if "PHOTO_IMPORT_LOG_FILE" in os.environ
        else None
    )
    lock_file: Path = Path(
        os.environ.get("PHOTO_IMPORT_LOCK_FILE", "/tmp/photo-import.lock")
    )
    mount_point: Path | None = field(default=None)
    destination_root: Path | None = field(default=None)
    read_only: bool = True
    supported_filesystems: tuple[str, ...] = ("exfat", "vfat", "fat32")
    required_dir_names: tuple[str, ...] = ("DCIM",)
    excluded_patterns: list[tuple[str, bool]] = field(
        default_factory=lambda: _IGNORE_PATTERNS
    )
    overwrite_existing: bool = False
    device_patterns: list[tuple[str, bool]] = field(
        default_factory=lambda: _DEVICE_PATTERNS
    )


class ConfigurationError(ValueError):
    pass


def load_config() -> Config:
    mount_point = os.environ.get("PHOTO_IMPORT_MOUNT_POINT")
    destination_root = os.environ.get("PHOTO_IMPORT_DESTINATION_ROOT")

    if not mount_point:
        raise ConfigurationError("PHOTO_IMPORT_MOUNT_POINT is not set")
    if not destination_root:
        raise ConfigurationError("PHOTO_IMPORT_DESTINATION_ROOT is not set")

    return Config(
        mount_point=Path(mount_point),
        destination_root=Path(destination_root),
    )
