from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import Config
from detect import CandidateDevice
from fnmatchplus import match

from sync import sync


@dataclass(frozen=True)
class SyncStats:
    synced_files: int = 0
    skipped: int = 0
    filtered_out: int = 0


def sync_media(config: Config, logger, device: CandidateDevice) -> SyncStats:
    assert config.mount_point is not None
    assert config.destination_root is not None

    mount_point = config.mount_point
    destination_root = config.destination_root

    destination_root.mkdir(parents=True, exist_ok=True)

    if not _has_required_layout(mount_point, config):
        raise RuntimeError(
            "mounted device "
            f"{device.path} does not contain any of {config.required_dir_names}"
        )

    filtered_out_count = 0

    def path_filter(path: Path) -> bool:
        if path.is_dir():
            _, excluded = match(path.name, config.excluded_patterns)
            return not excluded

        for parent in path.parents:
            _, excluded = match(parent.name, config.excluded_patterns)
            if excluded:
                return False

        matched, excluded = match(path.name, config.excluded_patterns)

        if excluded:
            return False
        if matched:
            return True

        nonlocal filtered_out_count
        filtered_out_count += 1
        return False

    sync_stats = sync(
        source=mount_point,
        destination=destination_root,
        filter=path_filter,
    )

    if sync_stats.copied:
        logger.info("synced %s files", sync_stats.copied)
    if sync_stats.skipped:
        logger.info("skipped %s existing files", sync_stats.skipped)

    return SyncStats(
        synced_files=sync_stats.copied,
        skipped=sync_stats.skipped,
        filtered_out=filtered_out_count,
    )


def _has_required_layout(mount_point: Path, config: Config) -> bool:
    return any((mount_point / name).is_dir() for name in config.required_dir_names)
