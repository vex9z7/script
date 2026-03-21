from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from config import Config
from fnmatchplus import match_any


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


def find_candidate_devices(config: Config) -> list[CandidateDevice]:
    data = get_lsblk()
    devices = flatten_blockdevices(data.get("blockdevices", []))
    candidates = []

    for device in devices:
        if not _is_candidate(device, config):
            continue
        candidates.append(_to_candidate(device))

    candidates.sort(key=lambda d: d.path)
    return candidates


def _is_candidate(device: dict, config: Config) -> bool:
    if device.get("type") != "part":
        return False

    fstype = (device.get("fstype") or "").lower()
    if fstype not in {fs.lower() for fs in config.supported_filesystems}:
        return False

    if device.get("mountpoint"):
        return False

    path = device.get("path")
    if not path or not match_any(path, config.device_patterns):
        return False

    if device.get("rm") not in (1, "1", True):
        return False

    transport = (device.get("tran") or "").lower()
    if transport not in {"usb", "mmc"}:
        return False

    return True


def _to_candidate(device: dict) -> CandidateDevice:
    rm = device.get("rm")
    removable = (
        False if rm in (0, "0", False) else (True if rm in (1, "1", True) else None)
    )

    return CandidateDevice(
        path=device["path"],
        fstype=(device.get("fstype") or "").lower(),
        label=device.get("label"),
        size=device.get("size"),
        removable=removable,
        model=device.get("model"),
        transport=device.get("tran"),
    )
