#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

from cleanup import safe_unmount
from config import ConfigurationError, load_config
from detect import find_candidate_devices
from mount import is_mountpoint, mount_device
from photo_sync import sync_media

from flockplus import FileLock
from log import build_logger


def main() -> int:
    try:
        config = load_config()
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    logger = build_logger("photo_import", log_file=config.log_file)

    if os.geteuid() != 0:
        logger.error("must run as root")
        return 1

    with FileLock(config.lock_file):
        mount_point = Path(config.mount_point)
        destination_root = Path(config.destination_root)

        if is_mountpoint(mount_point):
            logger.warning("mount point %s is already active", mount_point)
            return 1

        candidates = find_candidate_devices(config)
        if not candidates:
            logger.info("no suitable SD card candidate found")
            return 0

        for device in candidates:
            mounted = False
            try:
                mount_device(device.path, mount_point, read_only=config.read_only)
                mounted = True
                stats = sync_media(config, logger, device)
                logger.info(
                    "imported %s files from %s", stats.synced_files, device.label
                )
            except Exception as exc:
                logger.exception("device %s failed: %s", device.path, exc)
                if mounted:
                    safe_unmount(mount_point, logger)
                continue

            if mounted and not safe_unmount(mount_point, logger):
                return 1
            return 0

        logger.info("no suitable camera SD card was imported")
        return 0


if __name__ == "__main__":
    sys.exit(main())
