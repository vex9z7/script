from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SyncResult:
    copied: int = 0
    deleted: int = 0
    raw_output: tuple[str, ...] = ()


def sync(
    source: Path,
    destination: Path,
    *,
    filters: list[str] | None = None,
    delete: bool = True,
) -> SyncResult:
    if shutil.which("rsync") is None:
        raise RuntimeError("rsync is not available")

    source = Path(source)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)

    command = [
        "rsync",
        "-rlt",
        "--itemize-changes",
        "--out-format=%i %n",
        "--prune-empty-dirs",
    ]
    if delete:
        command.extend(["--delete", "--delete-excluded"])

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        filter_path = Path(handle.name)
        for rule in filters or []:
            handle.write(f"{rule}\n")

    try:
        command.extend(
            [f"--filter=merge {filter_path}", f"{source}/", str(destination)]
        )
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=True,
        )
    finally:
        filter_path.unlink(missing_ok=True)

    output_lines = tuple(
        line
        for line in result.stdout.splitlines()
        if line
        and not line.startswith("sending ")
        and not line.startswith("sent ")
        and not line.startswith("total size ")
    )

    copied = 0
    deleted = 0
    for line in output_lines:
        if line.startswith("*deleting "):
            deleted += 1
            continue

        itemized, _, _name = line.partition(" ")
        if len(itemized) >= 2 and itemized[1] == "f":
            copied += 1

    return SyncResult(copied=copied, deleted=deleted, raw_output=output_lines)
