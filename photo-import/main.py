#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from datetime import datetime

from cleanup import safe_unmount
from config import DEFAULT_CONFIG
from detect import find_candidate_devices
from logging_utils import build_logger, save_state
from mount import is_mountpoint, mount_device
from photo_copy import copy_media_files


def main() -> int:
    config = DEFAULT_CONFIG
    logger = build_logger(config.log_file)

    if os.geteuid() != 0:
        logger.error("must run as root")
        return 1

    if is_mountpoint(config.mount_point):
        logger.warning(
            "mount point %s is already active, refusing to reuse it",
            config.mount_point,
        )
        return 1

    candidates = find_candidate_devices(config)
    if not candidates:
        logger.info("no suitable SD card candidate found")
        return 0

    logger.info("found %s candidate device(s)", len(candidates))

    for device in candidates:
        logger.info(
            "trying device=%s label=%r size=%s rm=%s fstype=%s tran=%s",
            device.path,
            device.label,
            device.size,
            device.removable,
            device.fstype,
            device.transport,
        )

        mounted = False
        try:
            mount_device(device.path, config.mount_point, read_only=config.read_only)
            mounted = True

            stats = copy_media_files(config, logger, device)
            import_record = {
                "device": device.path,
                "label": device.label,
                "size": device.size,
                "fstype": device.fstype,
                "transport": device.transport,
                "mounted_at": datetime.now().isoformat(timespec="seconds"),
                "mount_point": str(config.mount_point),
                "destination_root": str(config.destination_root),
                "copied_files": stats.copied_files,
                "skipped_existing": stats.skipped_existing,
                "filtered_out": stats.filtered_out,
            }
            save_state(config.state_file, import_record)
        except Exception as exc:
            logger.exception("device %s failed: %s", device.path, exc)
            if mounted:
                safe_unmount(config.mount_point, logger)
            continue

        if mounted and not safe_unmount(config.mount_point, logger):
            return 1

        logger.info("import completed successfully: %s", import_record)
        return 0

    logger.info("no suitable camera SD card was imported")
    return 0


if __name__ == "__main__":
    sys.exit(main())
