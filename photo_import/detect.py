from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

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
    uuid: str | None
    partuuid: str | None
    size: str | None
    removable: bool | None
    model: str | None
    serial: str | None
    transport: str | None
    mountpoint: str | None
    device_id: str


# System dependency: requires `lsblk` from util-linux
def get_lsblk() -> dict:
    result = subprocess.run(
        [
            "lsblk",
            "-J",
            "-o",
            "NAME,PATH,FSTYPE,TYPE,MOUNTPOINT,LABEL,UUID,PARTUUID,RM,SIZE,MODEL,SERIAL,TRAN",
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


def _parent_device_map(
    devices: list[dict], parent: dict | None = None
) -> dict[str, dict]:
    parents = {}

    for device in devices:
        path = device.get("path")
        if path and parent is not None:
            parents[path] = parent
        parents.update(_parent_device_map(device.get("children") or [], device))

    return parents


def _normalize_id_part(value: str | None) -> str | None:
    if not value:
        return None
    normalized = re.sub(r"\s+", "_", value.strip().lower())
    normalized = re.sub(r"[^a-z0-9._-]", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip("_-")
    return normalized or None


def _device_id(device: dict, parent: dict | None) -> str:
    parts = [
        _normalize_id_part((device.get("model") or (parent or {}).get("model"))),
        _normalize_id_part((device.get("serial") or (parent or {}).get("serial"))),
        _normalize_id_part(device.get("fstype")),
        _normalize_id_part(device.get("uuid")),
        _normalize_id_part(device.get("partuuid")),
    ]
    resolved = [part for part in parts if part]
    if resolved:
        return "-".join(resolved)

    fallback = _normalize_id_part(Path(device["path"]).name)
    return fallback or "unknown-device"


def find_candidate_devices(
    config: Config, logger: logging.Logger | None = None
) -> list[CandidateDevice]:
    data = get_lsblk()
    blockdevices = data.get("blockdevices", [])
    devices = flatten_blockdevices(blockdevices)
    parent_map = _parent_device_map(blockdevices)
    candidates = []

    for device in devices:
        path = device.get("path")
        parent = parent_map.get(path) if path else None
        accepted, reason = _candidate_status(device, config, parent)
        path = path or device.get("name") or "<unknown>"

        if logger is not None:
            logger.debug("device %s %s", path, reason)

        if not accepted:
            continue
        candidates.append(_to_candidate(device, parent))

    candidates.sort(key=lambda d: d.path)
    return candidates


def _candidate_status(
    device: dict, config: Config, parent: dict | None = None
) -> tuple[bool, str]:
    if device.get("type") != "part":
        return False, f"rejected: type={device.get('type')}, expected part"

    fstype = (device.get("fstype") or "").lower()
    if fstype not in {fs.lower() for fs in config.supported_filesystems}:
        return False, f"rejected: unsupported filesystem {fstype or '<none>'}"

    path = device.get("path")
    if not path or not match_any(path, config.device_patterns):
        return False, "rejected: path does not match configured device patterns"

    if not _parse_rm(device.get("rm")):
        return False, f"rejected: rm={device.get('rm')}, not removable"

    transport = _effective_transport(device, parent)
    if transport and transport not in _REMOVABLE_TRANSPORTS:
        return False, f"rejected: unsupported transport {transport}"

    return True, (
        "accepted: "
        f"fstype={fstype}, label={device.get('label') or '<none>'}, "
        f"rm={device.get('rm')}, tran={transport or '<none>'}, "
        f"mountpoint={device.get('mountpoint') or '<none>'}"
    )


def _effective_transport(device: dict, parent: dict | None) -> str:
    transport = (device.get("tran") or "").lower()
    if transport:
        return transport

    if parent is None:
        return ""

    return (parent.get("tran") or "").lower()


def _to_candidate(device: dict, parent: dict | None = None) -> CandidateDevice:
    removable = _parse_rm(device.get("rm"))

    return CandidateDevice(
        path=device["path"],
        fstype=(device.get("fstype") or "").lower(),
        label=device.get("label"),
        uuid=device.get("uuid"),
        partuuid=device.get("partuuid"),
        size=device.get("size"),
        removable=removable,
        model=device.get("model") or (parent or {}).get("model"),
        serial=device.get("serial") or (parent or {}).get("serial"),
        transport=device.get("tran"),
        mountpoint=device.get("mountpoint"),
        device_id=_device_id(device, parent),
    )
