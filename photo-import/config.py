from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    mount_point: Path = Path("/mnt/camera-sd-card")
    destination_root: Path = Path("/mnt/tank/photo/import")
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
