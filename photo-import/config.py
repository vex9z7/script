from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import dotenv

dotenv.load_dotenv()

_THIS_DIR = Path(__file__).parent


def _load_ignore_list() -> tuple[frozenset[str], frozenset[str]]:
    path = _THIS_DIR / ".photoignore"
    dirs: set[str] = set()
    suffixes: set[str] = set()
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("dir:"):
                dirs.add(line[4:])
            elif line.startswith("suffix:"):
                suffixes.add(line[7:])
            else:
                dirs.add(line)
    return frozenset(dirs), frozenset(suffixes)


def _load_extensions() -> frozenset[str]:
    path = _THIS_DIR / ".photoextensions"
    if path.exists():
        return frozenset(
            line.strip()
            for line in path.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        )
    return frozenset()


_IGNORED_DIRS, _IGNORED_SUFFIXES = _load_ignore_list()
_ALLOWED_EXTENSIONS = _load_extensions()


@dataclass(frozen=True)
class Config:
    log_file: Path | None = (
        Path(os.environ.get("PHOTO_IMPORT_LOG_FILE", "/var/log/photo-import.log"))
        if os.environ.get("PHOTO_IMPORT_LOG_FILE")
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
    allowed_extensions: frozenset[str] = field(
        default_factory=lambda: _ALLOWED_EXTENSIONS
    )
    excluded_dir_names: frozenset[str] = field(default_factory=lambda: _IGNORED_DIRS)
    excluded_file_names: frozenset[str] = field(default_factory=frozenset)
    excluded_suffixes: frozenset[str] = field(default_factory=lambda: _IGNORED_SUFFIXES)
    overwrite_existing: bool = False


DEFAULT_CONFIG = Config()


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
