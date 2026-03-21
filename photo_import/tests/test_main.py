from __future__ import annotations

import importlib
import logging
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

from photo_import.config import Config
from photo_import.photo_sync import SyncStats
from photo_import.tests.conftest import make_mock_process_lock


def test_main_returns_zero_when_no_candidate_devices(monkeypatch, tmp_path):
    main_module = importlib.import_module("photo_import.app")
    config = Config(
        mount_root=tmp_path / "mount-root",
        import_root=tmp_path / "import-root",
    )

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "FileLock", make_mock_process_lock())
    monkeypatch.setattr(
        main_module, "find_candidate_devices", lambda _, logger=None: []
    )

    assert main_module.main() == 0


def test_main_runs_successful_import_flow(monkeypatch, tmp_path, candidate_device):
    main_module = importlib.import_module("photo_import.app")
    config = Config(
        mount_root=tmp_path / "mount-root",
        import_root=tmp_path / "import-root",
    )
    calls = []
    logger = MagicMock()

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(main_module, "build_logger", lambda *args, **kwargs: logger)
    monkeypatch.setattr(main_module, "FileLock", make_mock_process_lock())
    monkeypatch.setattr(
        main_module,
        "find_candidate_devices",
        lambda _, logger=None: [candidate_device],
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
        lambda config_value, logger_value, device_value, mount_path, destination_path: (
            calls.append(("sync", mount_path, destination_path, device_value.path))
            or SyncStats(synced_files=3, skipped=1, filtered_out=2)
        ),
    )
    monkeypatch.setattr(
        main_module,
        "safe_unmount",
        lambda mount_point, logger_value: calls.append(("unmount", mount_point))
        or True,
    )

    assert main_module.main() == 0
    derived_mount = config.mount_root / candidate_device.device_id
    derived_import = config.import_root / candidate_device.device_id
    assert calls[0] == ("mount", candidate_device.path, derived_mount, config.read_only)
    assert calls[1] == ("sync", derived_mount, derived_import, candidate_device.path)
    assert calls[2] == ("unmount", derived_mount)
    logger.info.assert_any_call(
        "mounting device %s at %s (read_only=%s)",
        candidate_device.path,
        derived_mount,
        config.read_only,
    )
    logger.info.assert_any_call("syncing %s to %s", derived_mount, derived_import)
    logger.debug.assert_any_call(
        "mounted device %s at %s", candidate_device.path, derived_mount
    )


def test_main_returns_one_when_unmount_fails(monkeypatch, tmp_path, candidate_device):
    main_module = importlib.import_module("photo_import.app")
    config = Config(
        mount_root=tmp_path / "mount-root",
        import_root=tmp_path / "import-root",
    )

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "FileLock", make_mock_process_lock())
    monkeypatch.setattr(
        main_module,
        "find_candidate_devices",
        lambda _, logger=None: [candidate_device],
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

    monkeypatch.delenv("PHOTO_IMPORT_MOUNT_ROOT", raising=False)
    monkeypatch.delenv("PHOTO_IMPORT_IMPORT_ROOT", raising=False)

    assert main_module.main() == 1


def test_main_package_runs_without_install(monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)

    env.pop("PHOTO_IMPORT_MOUNT_ROOT", None)
    env.pop("PHOTO_IMPORT_IMPORT_ROOT", None)

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
        mount_root=tmp_path / "mount-root",
        import_root=tmp_path / "import-root",
    )

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 1)
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )

    assert main_module.main() == 1


def test_main_reuses_existing_device_mountpoint(
    monkeypatch, tmp_path, candidate_device
):
    main_module = importlib.import_module("photo_import.app")
    mounted_candidate = candidate_device.__class__(
        **{**candidate_device.__dict__, "mountpoint": "/mnt/camera-sd-card"}
    )
    config = Config(
        mount_root=tmp_path / "mount-root",
        import_root=tmp_path / "import-root",
    )
    logger = MagicMock()
    mount_calls = []
    unmount_calls = []

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(main_module, "build_logger", lambda *args, **kwargs: logger)
    monkeypatch.setattr(main_module, "FileLock", make_mock_process_lock())
    monkeypatch.setattr(
        main_module,
        "find_candidate_devices",
        lambda _, logger=None: [mounted_candidate],
    )
    monkeypatch.setattr(
        main_module,
        "sync_media",
        lambda config_value,
        logger_value,
        device_value,
        mount_path,
        destination_path: SyncStats(
            synced_files=2,
            skipped=0,
            filtered_out=0,
        ),
    )
    monkeypatch.setattr(
        main_module,
        "mount_device",
        lambda *args, **kwargs: mount_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        main_module,
        "safe_unmount",
        lambda *args, **kwargs: unmount_calls.append((args, kwargs)) or True,
    )

    assert main_module.main() == 0
    assert not mount_calls
    assert not unmount_calls
    logger.info.assert_any_call(
        "reusing existing mount %s for %s",
        Path(mounted_candidate.mountpoint),
        mounted_candidate.path,
    )
    logger.info.assert_any_call(
        "syncing %s to %s",
        Path(mounted_candidate.mountpoint),
        config.import_root / mounted_candidate.device_id,
    )


def test_main_returns_one_when_reused_mount_sync_fails(
    monkeypatch, tmp_path, candidate_device
):
    main_module = importlib.import_module("photo_import.app")
    mounted_candidate = candidate_device.__class__(
        **{**candidate_device.__dict__, "mountpoint": "/mnt/camera-sd-card"}
    )
    config = Config(
        mount_root=tmp_path / "mount-root",
        import_root=tmp_path / "import-root",
    )
    mount_calls = []
    unmount_calls = []

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "FileLock", make_mock_process_lock())
    monkeypatch.setattr(
        main_module,
        "find_candidate_devices",
        lambda _, logger=None: [mounted_candidate],
    )
    monkeypatch.setattr(
        main_module,
        "sync_media",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("bad mount")),
    )
    monkeypatch.setattr(
        main_module,
        "mount_device",
        lambda *args, **kwargs: mount_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        main_module,
        "safe_unmount",
        lambda *args, **kwargs: unmount_calls.append((args, kwargs)) or True,
    )

    assert main_module.main() == 0
    assert not mount_calls
    assert not unmount_calls


def test_main_continues_to_next_device_when_one_fails(
    monkeypatch, tmp_path, candidate_device
):
    main_module = importlib.import_module("photo_import.app")
    config = Config(
        mount_root=tmp_path / "mount-root",
        import_root=tmp_path / "import-root",
    )

    call_count = {"sync_fail": 0}

    def mock_sync_that_fails(*args, **kwargs):
        del args, kwargs
        call_count["sync_fail"] += 1
        raise Exception("Sync failed")

    monkeypatch.setattr(main_module, "load_config", lambda: config)
    monkeypatch.setattr(main_module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        main_module, "build_logger", lambda *args, **kwargs: logging.getLogger("test")
    )
    monkeypatch.setattr(main_module, "FileLock", make_mock_process_lock())
    monkeypatch.setattr(
        main_module,
        "find_candidate_devices",
        lambda _, logger=None: [candidate_device],
    )
    monkeypatch.setattr(main_module, "mount_device", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_module, "sync_media", mock_sync_that_fails)
    monkeypatch.setattr(main_module, "safe_unmount", lambda *args, **kwargs: True)

    result = main_module.main()

    assert result == 0
    assert call_count["sync_fail"] == 1
