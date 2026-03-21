from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from photo_import.config import Config
from photo_import.detect import CandidateDevice
from scriptlib.fnmatchplus import match

from scriptlib.pyrsync import sync


@dataclass(frozen=True)
class SyncStats:
    synced_files: int = 0
    skipped: int = 0
    filtered_out: int = 0


def _is_excluded_dir(name: str, patterns: list[tuple[str, bool]]) -> bool:
    _, excluded = match(name, patterns)
    return excluded


def _is_included_file(name: str, patterns: list[tuple[str, bool]]) -> tuple[bool, bool]:
    matched, excluded = match(name, patterns)
    return matched and not excluded, matched and excluded


def _scan_source_tree(
    source: Path, patterns: list[tuple[str, bool]]
) -> tuple[int, int]:
    allowed_files = 0
    filtered_out = 0

    for root, dirs, files in os.walk(source):
        del root
        dirs[:] = [
            directory for directory in dirs if not _is_excluded_dir(directory, patterns)
        ]

        for filename in files:
            included, excluded = _is_included_file(filename, patterns)
            if included:
                allowed_files += 1
                continue
            if excluded:
                continue
            filtered_out += 1

    return allowed_files, filtered_out


def _rsync_filters(patterns: list[tuple[str, bool]]) -> list[str]:
    rules = []

    for pattern, excluded in patterns:
        if not excluded:
            continue
        rules.append(f"- {pattern}")
        rules.append(f"- {pattern}/***")

    rules.append("+ */")

    for pattern, excluded in patterns:
        if excluded:
            continue
        rules.append(f"+ {pattern}")

    rules.append("- *")
    return rules


def sync_media(
    config: Config,
    logger,
    device: CandidateDevice,
    mount_point: Path,
    destination_root: Path,
) -> SyncStats:
    destination_root.mkdir(parents=True, exist_ok=True)

    logger.debug(
        "starting sync from %s to %s for %s",
        mount_point,
        destination_root,
        device.path,
    )

    if not _has_required_layout(mount_point, config):
        raise RuntimeError(
            "mounted device "
            f"{device.path} does not contain any of {config.required_dir_names}"
        )

    allowed_files_count, filtered_out_count = _scan_source_tree(
        mount_point, config.excluded_patterns
    )
    filters = _rsync_filters(config.excluded_patterns)

    sync_stats = sync(
        source=mount_point,
        destination=destination_root,
        filters=filters,
    )
    skipped_count = max(0, allowed_files_count - sync_stats.copied)

    if sync_stats.copied:
        logger.info("synced %s files", sync_stats.copied)
    if skipped_count:
        logger.info("skipped %s existing files", skipped_count)
    logger.debug(
        "sync complete for %s: copied=%s skipped=%s filtered_out=%s",
        device.path,
        sync_stats.copied,
        skipped_count,
        filtered_out_count,
    )

    return SyncStats(
        synced_files=sync_stats.copied,
        skipped=skipped_count,
        filtered_out=filtered_out_count,
    )


def _has_required_layout(mount_point: Path, config: Config) -> bool:
    return any((mount_point / name).is_dir() for name in config.required_dir_names)
