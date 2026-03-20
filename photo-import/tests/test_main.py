from __future__ import annotations

import importlib
import logging
from contextlib import contextmanager

from config import Config
from detect import CandidateDevice
from photo_copy import CopyStats
from process_lock import ProcessLockBusyError


@contextmanager
def _noop_lock(_lock_file):
    yield


def test_main_returns_zero_when_no_candidate_devices(monkeypatch, tmp_path):
    main_module = importlib.import_module("main")
    config = Config(
        mount_point=tmp_path / "mount",
        destination_root=tmp_path / "dest",
    )

    monkeypatch.setattr(main_module, "DEFAULT_CONFIG", config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "process_lock", _noop_lock)
    monkeypatch.setattr(main_module, "is_mountpoint", lambda _: False)
    monkeypatch.setattr(main_module, "find_candidate_devices", lambda _: [])

    assert main_module.main() == 0


def test_main_runs_successful_import_flow(monkeypatch, tmp_path):
    main_module = importlib.import_module("main")
    config = Config(
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
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "process_lock", _noop_lock)
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
        "safe_unmount",
        lambda mount_point, logger: calls.append(("unmount", mount_point)) or True,
    )

    assert main_module.main() == 0
    assert calls[0] == ("mount", device.path, config.mount_point, config.read_only)
    assert calls[1] == ("copy", config.destination_root, device.path)
    assert calls[2] == ("unmount", config.mount_point)


def test_main_returns_one_when_unmount_fails(monkeypatch, tmp_path):
    main_module = importlib.import_module("main")
    config = Config(
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
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "process_lock", _noop_lock)
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
    monkeypatch.setattr(main_module, "safe_unmount", lambda *args, **kwargs: False)

    assert main_module.main() == 1


def test_main_returns_zero_when_lock_is_busy(monkeypatch, tmp_path):
    main_module = importlib.import_module("main")
    config = Config(
        lock_file=tmp_path / "photo-import.lock",
        mount_point=tmp_path / "mount",
        destination_root=tmp_path / "dest",
    )

    @contextmanager
    def busy_lock(_lock_file):
        raise ProcessLockBusyError("busy")
        yield

    monkeypatch.setattr(main_module, "DEFAULT_CONFIG", config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "process_lock", busy_lock)

    assert main_module.main() == 0
