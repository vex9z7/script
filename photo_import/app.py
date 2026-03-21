from __future__ import annotations

import os
import sys
from pathlib import Path

from photo_import.cleanup import safe_unmount
from photo_import.config import ConfigurationError, load_config
from photo_import.detect import find_candidate_devices
from photo_import.mount import mount_device
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
    assert config.mount_root is not None
    assert config.import_root is not None

    mount_root = config.mount_root
    import_root = config.import_root

    if os.geteuid() != 0:
        logger.error("must run as root")
        return 1

    with FileLock(config.lock_file):
        candidates = find_candidate_devices(config, logger=logger)
        if not candidates:
            logger.info("no suitable SD card candidate found")
            return 0

        for device in candidates:
            mount_point = (
                Path(device.mountpoint)
                if device.mountpoint
                else mount_root / device.device_id
            )
            destination_root = import_root / device.device_id
            mounted_by_run = device.mountpoint is None

            try:
                if mounted_by_run:
                    logger.info(
                        "mounting device %s at %s (read_only=%s)",
                        device.path,
                        mount_point,
                        config.read_only,
                    )
                    mount_device(device.path, mount_point, read_only=config.read_only)
                    logger.debug("mounted device %s at %s", device.path, mount_point)
                else:
                    logger.info(
                        "reusing existing mount %s for %s", mount_point, device.path
                    )

                logger.info("syncing %s to %s", mount_point, destination_root)
                stats = sync_media(
                    config, logger, device, mount_point, destination_root
                )
                logger.info(
                    "imported %s files from %s into %s",
                    stats.synced_files,
                    device.label,
                    destination_root,
                )
            except Exception as exc:
                logger.exception("device %s failed: %s", device.path, exc)
                if mounted_by_run:
                    safe_unmount(mount_point, logger)
                continue

            if mounted_by_run and not safe_unmount(mount_point, logger):
                return 1
            return 0

        logger.info("no suitable camera SD card was imported")
        return 0
