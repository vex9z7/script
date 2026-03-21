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

    source_files: set[Path] = set()

    for root, dirs, files in os.walk(source):
        root_path = Path(root)

        if filter is not None:
            dirs[:] = [d for d in dirs if filter(root_path / d)]

        for filename in files:
            src_file = root_path / filename
            dst_file = destination / src_file.relative_to(source)

            if filter is not None and not filter(src_file):
                continue

            source_files.add(dst_file)
            dst_file.parent.mkdir(parents=True, exist_ok=True)

            if _should_skip(src_file, dst_file, strict):
                stats.skipped += 1
                continue

            shutil.copy2(src_file, dst_file)
            stats.copied += 1

    for root, _dirs, files in os.walk(destination):
        root_path = Path(root)
        for filename in files:
            dst_file = root_path / filename
            if dst_file not in source_files:
                dst_file.unlink()
                stats.deleted += 1

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
