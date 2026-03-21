from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass

from photo_import.config import Config
from scriptlib.fnmatchplus import match_any


_REMOVABLE_TRANSPORTS = {"usb", "mmc"}


def _parse_rm(value: object) -> bool | None:
    if value in (0, "0", False):
        return False
    if value in (1, "1", True):
        return True
    return None


@dataclass(frozen=True)
class CandidateDevice:
    path: str
    fstype: str
    label: str | None
    size: str | None
    removable: bool | None
    model: str | None
    transport: str | None


# System dependency: requires `lsblk` from util-linux
def get_lsblk() -> dict:
    result = subprocess.run(
        [
            "lsblk",
            "-J",
            "-o",
            "NAME,PATH,FSTYPE,TYPE,MOUNTPOINT,LABEL,RM,SIZE,MODEL,TRAN",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def flatten_blockdevices(devices: list[dict]) -> list[dict]:
    result = []
    for d in devices:
        result.append(d)
        result.extend(flatten_blockdevices(d.get("children") or []))
    return result


def find_candidate_devices(
    config: Config, logger: logging.Logger | None = None
) -> list[CandidateDevice]:
    data = get_lsblk()
    devices = flatten_blockdevices(data.get("blockdevices", []))
    candidates = []

    for device in devices:
        accepted, reason = _candidate_status(device, config)
        path = device.get("path") or device.get("name") or "<unknown>"

        if logger is not None:
            logger.debug("device %s %s", path, reason)

        if not accepted:
            continue
        candidates.append(_to_candidate(device))

    candidates.sort(key=lambda d: d.path)
    return candidates


def _candidate_status(device: dict, config: Config) -> tuple[bool, str]:
    if device.get("type") != "part":
        return False, f"rejected: type={device.get('type')}, expected part"

    fstype = (device.get("fstype") or "").lower()
    if fstype not in {fs.lower() for fs in config.supported_filesystems}:
        return False, f"rejected: unsupported filesystem {fstype or '<none>'}"

    if device.get("mountpoint"):
        return False, f"rejected: already mounted at {device.get('mountpoint')}"

    path = device.get("path")
    if not path or not match_any(path, config.device_patterns):
        return False, "rejected: path does not match configured device patterns"

    if not _parse_rm(device.get("rm")):
        return False, f"rejected: rm={device.get('rm')}, not removable"

    transport = (device.get("tran") or "").lower()
    if transport not in _REMOVABLE_TRANSPORTS:
        return False, f"rejected: unsupported transport {transport or '<none>'}"

    return True, (
        "accepted: "
        f"fstype={fstype}, label={device.get('label') or '<none>'}, "
        f"rm={device.get('rm')}, tran={transport}"
    )


def _to_candidate(device: dict) -> CandidateDevice:
    removable = _parse_rm(device.get("rm"))

    return CandidateDevice(
        path=device["path"],
        fstype=(device.get("fstype") or "").lower(),
        label=device.get("label"),
        size=device.get("size"),
        removable=removable,
        model=device.get("model"),
        transport=device.get("tran"),
    )
