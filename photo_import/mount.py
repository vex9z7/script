from __future__ import annotations

import subprocess
from pathlib import Path


# System dependencies: requires mountpoint, mount, umount from util-linux
def is_mountpoint(path: Path) -> bool:
    result = subprocess.run(
        ["mountpoint", "-q", str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def mount_device(device: str, mount_point: Path, *, read_only: bool) -> None:
    mount_point.mkdir(parents=True, exist_ok=True)
    options = "ro" if read_only else "rw"
    subprocess.run(
        ["mount", "-o", options, device, str(mount_point)],
        text=True,
        capture_output=True,
        check=True,
    )


def unmount_device(mount_point: Path) -> None:
    subprocess.run(
        ["umount", str(mount_point)],
        text=True,
        capture_output=True,
        check=True,
    )
