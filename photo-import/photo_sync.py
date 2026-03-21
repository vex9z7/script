from __future__ import annotations

import fnmatch
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


def _matches(name: str, patterns: list[tuple[str, bool]]) -> tuple[bool, bool]:
    """Check if name matches patterns (fnmatch-style, last match wins).

    Returns (matches, excluded) tuple.
    - matches: True if name matches any pattern
    - excluded: True if the last matching pattern is an exclusion (starts with !)
    """
    matched = False
    excluded = False
    for pattern, is_excluded in patterns:
        if fnmatch.fnmatch(name, pattern):
            matched = True
            excluded = is_excluded
    return matched, excluded


def sync_media(config: Config, logger, device: CandidateDevice) -> SyncStats:
    mount_point = config.mount_point
    destination_root = config.destination_root
    destination_root.mkdir(parents=True, exist_ok=True)

    if not _has_required_layout(mount_point, config):
        raise RuntimeError(
            "mounted device "
            f"{device.path} does not contain any of {config.required_dir_names}"
        )

    filtered_out_count = 0

    def filter(path: Path) -> bool:
        if path.is_dir():
            matched, excluded = _matches(path.name, config.excluded_patterns)
            return not excluded

        # Check if any parent directory is excluded
        for parent in path.parents:
            matched, excluded = _matches(parent.name, config.excluded_patterns)
            if excluded:
                return False

        # Check if filename matches a pattern
        matched, excluded = _matches(path.name, config.excluded_patterns)

        if excluded:
            return False

        if matched:
            return True

        # No match means filtered out
        nonlocal filtered_out_count
        filtered_out_count += 1
        return False

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
