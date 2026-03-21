from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

_THIS_DIR = Path(__file__).parent


def _optional_path(env: Mapping[str, str], name: str) -> Path | None:
    value = env.get(name)
    if not value:
        return None
    return Path(value)


def _required_path(env: Mapping[str, str], name: str) -> Path:
    value = env.get(name)
    if not value:
        raise ConfigurationError(f"{name} is not set")
    return Path(value)


def _log_level(env: Mapping[str, str], name: str) -> int:
    value = (env.get(name) or "INFO").strip().upper()
    level = getattr(logging, value, None)
    if not isinstance(level, int):
        raise ConfigurationError(f"{name} is invalid: {value}")
    return level


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
    log_file: Path | None = None
    log_level: int = logging.INFO
    lock_file: Path = Path()
    mount_root: Path | None = field(default=None)
    import_root: Path | None = field(default=None)
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


def load_config(env: Mapping[str, str] | None = None) -> Config:
    env_values = os.environ if env is None else env

    mount_root = env_values.get("PHOTO_IMPORT_MOUNT_ROOT")
    import_root = env_values.get("PHOTO_IMPORT_IMPORT_ROOT")

    if not mount_root:
        raise ConfigurationError("PHOTO_IMPORT_MOUNT_ROOT is not set")
    if not import_root:
        raise ConfigurationError("PHOTO_IMPORT_IMPORT_ROOT is not set")

    return Config(
        log_file=_optional_path(env_values, "PHOTO_IMPORT_LOG_FILE"),
        log_level=_log_level(env_values, "PHOTO_IMPORT_LOG_LEVEL"),
        lock_file=_required_path(env_values, "PHOTO_IMPORT_LOCK_FILE"),
        mount_root=Path(mount_root),
        import_root=Path(import_root),
    )
