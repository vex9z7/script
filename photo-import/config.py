from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import dotenv

dotenv.load_dotenv()


@dataclass(frozen=True)
class Config:
    lock_file: Path = Path(
        os.environ.get("PHOTO_IMPORT_LOCK_FILE", "/tmp/photo-import.lock")
    )
    mount_point: Path = Path(
        os.environ.get("PHOTO_IMPORT_MOUNT_POINT", "/mnt/camera-sd-card")
    )
    destination_root: Path = Path(
        os.environ.get("PHOTO_IMPORT_DESTINATION_ROOT", "/mnt/tank/photo/import")
    )
    read_only: bool = True
    supported_filesystems: tuple[str, ...] = ("exfat", "vfat", "fat32")
    required_dir_names: tuple[str, ...] = ("DCIM",)
    allowed_extensions: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                ".jpg",
                ".jpeg",
                ".png",
                ".heic",
                ".arw",
                ".cr2",
                ".cr3",
                ".nef",
                ".dng",
                ".raf",
                ".rw2",
                ".orf",
                ".mp4",
                ".mov",
                ".mts",
                ".m2ts",
                ".avi",
            }
        )
    )
    excluded_dir_names: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "@eadir",
                ".trashes",
                ".spotlight-v100",
                "thumb",
                "thumbs",
                "thumbnail",
                "thumbnails",
            }
        )
    )
    excluded_file_names: frozenset[str] = field(default_factory=frozenset)
    excluded_suffixes: frozenset[str] = field(
        default_factory=lambda: frozenset({".thm", ".thumb"})
    )
    overwrite_existing: bool = False


DEFAULT_CONFIG = Config()
