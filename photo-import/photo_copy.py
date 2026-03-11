from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from config import Config
from detect import CandidateDevice


@dataclass(frozen=True)
class CopyStats:
    copied_files: int = 0
    skipped_existing: int = 0
    filtered_out: int = 0


def copy_media_files(config: Config, logger, device: CandidateDevice) -> CopyStats:
    mount_point = config.mount_point
    destination_root = config.destination_root
    destination_root.mkdir(parents=True, exist_ok=True)

    if not _has_required_layout(mount_point, config):
        raise RuntimeError(
            "mounted device "
            f"{device.path} does not contain any of {config.required_dir_names}"
        )

    copied_files = 0
    skipped_existing = 0
    filtered_out = 0

    excluded_dirs = {name.lower() for name in config.excluded_dir_names}
    excluded_files = {name.lower() for name in config.excluded_file_names}
    excluded_suffixes = {suffix.lower() for suffix in config.excluded_suffixes}
    allowed_extensions = {suffix.lower() for suffix in config.allowed_extensions}

    for root, dirnames, filenames in os.walk(mount_point):
        dirnames[:] = [
            dirname for dirname in dirnames if dirname.lower() not in excluded_dirs
        ]

        root_path = Path(root)
        for filename in filenames:
            source = root_path / filename
            suffix = source.suffix.lower()

            if filename.lower() in excluded_files or suffix in excluded_suffixes:
                filtered_out += 1
                continue

            if suffix not in allowed_extensions:
                filtered_out += 1
                continue

            relative_path = source.relative_to(mount_point)
            destination = destination_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)

            if destination.exists() and not config.overwrite_existing:
                skipped_existing += 1
                logger.info("skipping existing file %s", destination)
                continue

            shutil.copy2(source, destination)
            copied_files += 1
            logger.info("copied %s -> %s", source, destination)

    return CopyStats(
        copied_files=copied_files,
        skipped_existing=skipped_existing,
        filtered_out=filtered_out,
    )


def _has_required_layout(mount_point: Path, config: Config) -> bool:
    return any((mount_point / name).is_dir() for name in config.required_dir_names)
