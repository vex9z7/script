from __future__ import annotations

import importlib
import logging

from config import Config
from detect import CandidateDevice
from photo_copy import CopyStats


def test_main_returns_zero_when_no_candidate_devices(monkeypatch, tmp_path):
    main_module = importlib.import_module("main")
    config = Config(
        base_dir=tmp_path / "base",
        mount_point=tmp_path / "mount",
        destination_root=tmp_path / "dest",
    )

    monkeypatch.setattr(main_module, "DEFAULT_CONFIG", config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda _: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "is_mountpoint", lambda _: False)
    monkeypatch.setattr(main_module, "find_candidate_devices", lambda _: [])

    assert main_module.main() == 0


def test_main_runs_successful_import_flow(monkeypatch, tmp_path):
    main_module = importlib.import_module("main")
    config = Config(
        base_dir=tmp_path / "base",
        mount_point=tmp_path / "mount",
        destination_root=tmp_path / "dest",
    )
    device = CandidateDevice(
        path="/dev/mmcblk0p1",
        fstype="exfat",
        label="CARD",
        size="32G",
        removable=True,
        model=None,
        transport="mmc",
    )
    calls = []

    monkeypatch.setattr(main_module, "DEFAULT_CONFIG", config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda _: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "is_mountpoint", lambda _: False)
    monkeypatch.setattr(main_module, "find_candidate_devices", lambda _: [device])
    monkeypatch.setattr(
        main_module,
        "mount_device",
        lambda path, mount_point, read_only: calls.append(
            ("mount", path, mount_point, read_only)
        ),
    )
    monkeypatch.setattr(
        main_module,
        "copy_media_files",
        lambda config_value, logger, device_value: (
            calls.append(("copy", config_value.destination_root, device_value.path))
            or CopyStats(copied_files=3, skipped_existing=1, filtered_out=2)
        ),
    )
    monkeypatch.setattr(
        main_module,
        "save_state",
        lambda state_file, state: calls.append(("save_state", state_file, state)),
    )
    monkeypatch.setattr(
        main_module,
        "safe_unmount",
        lambda mount_point, logger: calls.append(("unmount", mount_point)) or True,
    )

    assert main_module.main() == 0
    assert calls[0] == ("mount", device.path, config.mount_point, config.read_only)
    assert calls[1] == ("copy", config.destination_root, device.path)
    assert calls[2][0] == "save_state"
    assert calls[3] == ("unmount", config.mount_point)


def test_main_returns_one_when_unmount_fails(monkeypatch, tmp_path):
    main_module = importlib.import_module("main")
    config = Config(
        base_dir=tmp_path / "base",
        mount_point=tmp_path / "mount",
        destination_root=tmp_path / "dest",
    )
    device = CandidateDevice(
        path="/dev/mmcblk0p1",
        fstype="exfat",
        label="CARD",
        size="32G",
        removable=True,
        model=None,
        transport="mmc",
    )

    monkeypatch.setattr(main_module, "DEFAULT_CONFIG", config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda _: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "is_mountpoint", lambda _: False)
    monkeypatch.setattr(main_module, "find_candidate_devices", lambda _: [device])
    monkeypatch.setattr(main_module, "mount_device", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        main_module,
        "copy_media_files",
        lambda *args, **kwargs: CopyStats(
            copied_files=1, skipped_existing=0, filtered_out=0
        ),
    )
    monkeypatch.setattr(main_module, "save_state", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_module, "safe_unmount", lambda *args, **kwargs: False)

    assert main_module.main() == 1
