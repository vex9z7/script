import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from fingerprint import fingerprints_match, get_fingerprint


@dataclass
class SyncStats:
    copied: int = 0
    skipped: int = 0
    deleted: int = 0


def sync(
    source: Path,
    destination: Path,
    filter: Callable[[Path], bool] | None = None,
    strict: bool = False,
) -> SyncStats:
    stats = SyncStats()
    source = Path(source)
    destination = Path(destination)

    def sync_directory(
        source_dir: Path, destination_dir: Path, is_root: bool = False
    ) -> None:
        if not source_dir.exists():
            return

        destination_preexisting = destination_dir.exists() and destination_dir.is_dir()

        if destination_dir.exists() and destination_dir.is_file():
            destination_dir.unlink()
            stats.deleted += 1

        destination_dir.mkdir(parents=True, exist_ok=True)

        if (
            not strict
            and not is_root
            and destination_preexisting
            and _should_skip_directory(source_dir, destination_dir)
        ):
            stats.skipped += 1
            return

        source_entries = {}

        for src_entry in source_dir.iterdir():
            if filter is not None and not filter(src_entry):
                continue

            source_entries[src_entry.name] = src_entry

        for name, src_entry in source_entries.items():
            dst_entry = destination_dir / name

            if src_entry.is_dir():
                sync_directory(src_entry, dst_entry)
                continue

            if dst_entry.exists() and dst_entry.is_dir():
                _delete_extra_tree(dst_entry, stats)
                dst_entry.rmdir()

            if _should_skip(src_entry, dst_entry, strict):
                stats.skipped += 1
                continue

            dst_entry.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_entry, dst_entry)
            stats.copied += 1

        for dst_entry in destination_dir.iterdir():
            if dst_entry.name in source_entries:
                continue

            if dst_entry.is_dir():
                _delete_extra_tree(dst_entry, stats)
                continue

            dst_entry.unlink()
            stats.deleted += 1

    sync_directory(source, destination, is_root=True)

    return stats


def _should_skip(source: Path, destination: Path, strict: bool) -> bool:
    if not destination.exists():
        return False

    src_fp = get_fingerprint(source)
    dst_fp = get_fingerprint(destination)

    if not fingerprints_match(src_fp, dst_fp):
        return False

    if not strict:
        return True

    return _files_match_strict(source, destination)


def _files_match_strict(source: Path, destination: Path) -> bool:
    with (
        source.open("rb") as source_handle,
        destination.open("rb") as destination_handle,
    ):
        while True:
            source_chunk = source_handle.read(8192)
            destination_chunk = destination_handle.read(8192)

            if source_chunk != destination_chunk:
                return False

            if not source_chunk:
                return True


def _should_skip_directory(source: Path, destination: Path) -> bool:
    if not destination.exists() or not destination.is_dir():
        return False

    src_fp = get_fingerprint(source)
    dst_fp = get_fingerprint(destination)

    return fingerprints_match(src_fp, dst_fp)


def _delete_extra_tree(path: Path, stats: SyncStats) -> None:
    for child in path.iterdir():
        if child.is_dir():
            _delete_extra_tree(child, stats)
            child.rmdir()
            continue

        child.unlink()
        stats.deleted += 1
