from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import Config
from detect import CandidateDevice

from sync import sync


@dataclass(frozen=True)
class SyncStats:
    synced_files: int = 0
    skipped: int = 0
    filtered_out: int = 0


def sync_media(config: Config, logger, device: CandidateDevice) -> SyncStats:
    mount_point = config.mount_point
    destination_root = config.destination_root
    destination_root.mkdir(parents=True, exist_ok=True)

    if not _has_required_layout(mount_point, config):
        raise RuntimeError(
            "mounted device "
            f"{device.path} does not contain any of {config.required_dir_names}"
        )

    excluded_dirs = {name.lower() for name in config.excluded_dir_names}
    excluded_files = {name.lower() for name in config.excluded_file_names}
    excluded_suffixes = {suffix.lower() for suffix in config.excluded_suffixes}
    allowed_extensions = {suffix.lower() for suffix in config.allowed_extensions}

    filtered_out_count = 0

    def filter(path: Path) -> bool:
        if path.is_dir():
            if path.name.lower() in excluded_dirs:
                return False
            return True
        if path.name.lower() in excluded_files:
            return False
        if path.suffix.lower() in excluded_suffixes:
            return False
        if path.suffix.lower() not in allowed_extensions:
            nonlocal filtered_out_count
            filtered_out_count += 1
            return False
        return True

    sync_stats = sync(
        source=mount_point,
        destination=destination_root,
        filter=filter,
    )

    for _ in range(sync_stats.copied):
        logger.info("synced file")

    for _ in range(sync_stats.skipped):
        logger.info("skipped existing file")

    return SyncStats(
        synced_files=sync_stats.copied,
        skipped=sync_stats.skipped,
        filtered_out=filtered_out_count,
    )


def _has_required_layout(mount_point: Path, config: Config) -> bool:
    return any((mount_point / name).is_dir() for name in config.required_dir_names)
