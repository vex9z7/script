from __future__ import annotations

import os
import sys

from photo_import.cleanup import safe_unmount
from photo_import.config import ConfigurationError, load_config
from photo_import.detect import find_candidate_devices
from photo_import.mount import is_mountpoint, mount_device
from photo_import.photo_sync import sync_media

from scriptlib.flockplus import FileLock
from scriptlib.log import build_logger


def main() -> int:
    try:
        config = load_config()
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    logger = build_logger(
        "photo_import",
        level=config.log_level,
        log_file=config.log_file,
    )
    assert config.mount_point is not None

    mount_point = config.mount_point

    if os.geteuid() != 0:
        logger.error("must run as root")
        return 1

    with FileLock(config.lock_file):
        if is_mountpoint(mount_point):
            logger.warning("mount point %s is already active", mount_point)
            return 1

        candidates = find_candidate_devices(config, logger=logger)
        if not candidates:
            logger.info("no suitable SD card candidate found")
            return 0

        for device in candidates:
            try:
                mount_device(device.path, mount_point, read_only=config.read_only)
                stats = sync_media(config, logger, device)
                logger.info(
                    "imported %s files from %s", stats.synced_files, device.label
                )
            except Exception as exc:
                logger.exception("device %s failed: %s", device.path, exc)
                safe_unmount(mount_point, logger)
                continue

            if not safe_unmount(mount_point, logger):
                return 1
            return 0

        logger.info("no suitable camera SD card was imported")
        return 0
