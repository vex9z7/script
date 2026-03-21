from __future__ import annotations

import importlib
import logging
import os
import subprocess
import sys
from pathlib import Path

from photo_import.config import Config
from photo_import.tests.conftest import make_mock_process_lock
from photo_import.photo_sync import SyncStats


def test_main_returns_zero_when_no_candidate_devices(monkeypatch, tmp_path):
    main_module = importlib.import_module("photo_import.app")
    config = Config(
        mount_point=tmp_path / "mount",
        destination_root=tmp_path / "dest",
    )

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "FileLock", make_mock_process_lock())
    monkeypatch.setattr(main_module, "is_mountpoint", lambda _: False)
    monkeypatch.setattr(main_module, "find_candidate_devices", lambda _: [])

    assert main_module.main() == 0


def test_main_runs_successful_import_flow(monkeypatch, tmp_path, candidate_device):
    main_module = importlib.import_module("photo_import.app")
    config = Config(
        mount_point=tmp_path / "mount",
        destination_root=tmp_path / "dest",
    )
    calls = []

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "FileLock", make_mock_process_lock())
    monkeypatch.setattr(main_module, "is_mountpoint", lambda _: False)
    monkeypatch.setattr(
        main_module, "find_candidate_devices", lambda _: [candidate_device]
    )
    monkeypatch.setattr(
        main_module,
        "mount_device",
        lambda path, mount_point, read_only: calls.append(
            ("mount", path, mount_point, read_only)
        ),
    )
    monkeypatch.setattr(
        main_module,
        "sync_media",
        lambda config_value, logger, device_value: (
            calls.append(("sync", config_value.destination_root, device_value.path))
            or SyncStats(synced_files=3, skipped=1, filtered_out=2)
        ),
    )
    monkeypatch.setattr(
        main_module,
        "safe_unmount",
        lambda mount_point, logger: calls.append(("unmount", mount_point)) or True,
    )

    assert main_module.main() == 0
    assert calls[0] == (
        "mount",
        candidate_device.path,
        config.mount_point,
        config.read_only,
    )
    assert calls[1] == ("sync", config.destination_root, candidate_device.path)
    assert calls[2] == ("unmount", config.mount_point)


def test_main_returns_one_when_unmount_fails(monkeypatch, tmp_path, candidate_device):
    main_module = importlib.import_module("photo_import.app")
    config = Config(
        mount_point=tmp_path / "mount",
        destination_root=tmp_path / "dest",
    )

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "FileLock", make_mock_process_lock())
    monkeypatch.setattr(main_module, "is_mountpoint", lambda _: False)
    monkeypatch.setattr(
        main_module, "find_candidate_devices", lambda _: [candidate_device]
    )
    monkeypatch.setattr(main_module, "mount_device", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        main_module,
        "sync_media",
        lambda *args, **kwargs: SyncStats(synced_files=1, skipped=0, filtered_out=0),
    )
    monkeypatch.setattr(main_module, "safe_unmount", lambda *args, **kwargs: False)

    assert main_module.main() == 1


def test_main_returns_one_when_config_missing(monkeypatch):
    main_module = importlib.import_module("photo_import.app")

    monkeypatch.delenv("PHOTO_IMPORT_MOUNT_POINT", raising=False)
    monkeypatch.delenv("PHOTO_IMPORT_DESTINATION_ROOT", raising=False)

    assert main_module.main() == 1


def test_main_package_runs_without_install(monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)

    env.pop("PHOTO_IMPORT_MOUNT_POINT", None)
    env.pop("PHOTO_IMPORT_DESTINATION_ROOT", None)

    result = subprocess.run(
        [sys.executable, "-m", "photo_import"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 1
    assert "Configuration error:" in result.stderr
    assert "ModuleNotFoundError" not in result.stderr


def test_main_returns_one_when_not_root(monkeypatch, tmp_path):
    main_module = importlib.import_module("photo_import.app")
    config = Config(
        mount_point=tmp_path / "mount",
        destination_root=tmp_path / "dest",
    )

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 1)  # non-zero = not root
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )

    assert main_module.main() == 1


def test_main_returns_one_when_mount_point_already_active(monkeypatch, tmp_path):
    main_module = importlib.import_module("photo_import.app")
    config = Config(
        mount_point=tmp_path / "mount",
        destination_root=tmp_path / "dest",
    )

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "FileLock", make_mock_process_lock())
    monkeypatch.setattr(main_module, "is_mountpoint", lambda _: True)  # already mounted

    assert main_module.main() == 1


def test_main_continues_to_next_device_when_one_fails(
    monkeypatch, tmp_path, candidate_device
):
    main_module = importlib.import_module("photo_import.app")
    config = Config(
        mount_point=tmp_path / "mount",
        destination_root=tmp_path / "dest",
    )

    call_count = {"mount": 0, "sync_fail": 0}

    def mock_sync_that_fails(*args, **kwargs):
        call_count["sync_fail"] += 1
        raise Exception("Sync failed")

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "FileLock", make_mock_process_lock())
    monkeypatch.setattr(main_module, "is_mountpoint", lambda _: False)
    monkeypatch.setattr(
        main_module, "find_candidate_devices", lambda _: [candidate_device]
    )
    monkeypatch.setattr(main_module, "mount_device", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_module, "sync_media", mock_sync_that_fails)
    monkeypatch.setattr(main_module, "safe_unmount", lambda *args, **kwargs: True)

    result = main_module.main()

    assert result == 0  # returns 0 after logging error when all devices fail
    assert call_count["sync_fail"] == 1
