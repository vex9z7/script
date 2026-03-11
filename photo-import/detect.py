from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from config import Config


@dataclass(frozen=True)
class CandidateDevice:
    path: str
    fstype: str
    label: str | None
    size: str | None
    removable: bool | None
    model: str | None
    transport: str | None


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=True)


def get_lsblk() -> dict:
    result = run(
        [
            "lsblk",
            "-J",
            "-o",
            "NAME,PATH,FSTYPE,TYPE,MOUNTPOINT,LABEL,RM,SIZE,MODEL,TRAN",
        ]
    )
    return json.loads(result.stdout)


def flatten_blockdevices(devices: list[dict]) -> list[dict]:
    flattened: list[dict] = []

    def walk(device: dict) -> None:
        flattened.append(device)
        for child in device.get("children", []) or []:
            walk(child)

    for device in devices:
        walk(device)
    return flattened


def find_candidate_devices(config: Config) -> list[CandidateDevice]:
    data = get_lsblk()
    devices = flatten_blockdevices(data.get("blockdevices", []))
    candidates: list[CandidateDevice] = []
    supported_filesystems = {value.lower() for value in config.supported_filesystems}

    for device in devices:
        if device.get("type") != "part":
            continue

        fstype = (device.get("fstype") or "").lower()
        if fstype not in supported_filesystems:
            continue

        if device.get("mountpoint"):
            continue

        path = device.get("path")
        if not path:
            continue

        candidates.append(
            CandidateDevice(
                path=path,
                fstype=fstype,
                label=device.get("label"),
                size=device.get("size"),
                removable=_to_bool(device.get("rm")),
                model=device.get("model"),
                transport=device.get("tran"),
            )
        )

    candidates.sort(key=_candidate_sort_key)
    return candidates


def _to_bool(value: object) -> bool | None:
    if value in (0, "0", False):
        return False
    if value in (1, "1", True):
        return True
    return None


def _candidate_sort_key(device: CandidateDevice) -> tuple[int, int, str]:
    removable_score = 0 if device.removable else 1
    transport_score = 0 if (device.transport or "").lower() in {"usb", "mmc"} else 1
    return (removable_score, transport_score, device.path)
