from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    base_dir: Path = Path("/mnt/tank/automation/photo-import")
    mount_point: Path = Path("/mnt/photo_sd")
    destination_root: Path = Path("/mnt/tank/photo-import")
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

    @property
    def log_file(self) -> Path:
        return self.base_dir / "logs" / "photo_import.log"

    @property
    def state_file(self) -> Path:
        return self.base_dir / "state" / "last_import.json"


DEFAULT_CONFIG = Config()
