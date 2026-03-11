from __future__ import annotations

from pathlib import Path

from mount import is_mountpoint, unmount_device


def safe_unmount(mount_point: Path, logger) -> bool:
    if not is_mountpoint(mount_point):
        return True

    try:
        unmount_device(mount_point)
        logger.info("unmounted %s", mount_point)
        return True
    except Exception as exc:
        logger.exception("failed to unmount %s: %s", mount_point, exc)
        return False
