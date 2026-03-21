from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from config import Config
from detect import find_candidate_devices, get_lsblk, run, _to_bool


class TestRun:
    def test_should_call_subprocess_with_correct_args(self):
        # Arrange
        with patch("detect.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="ok", returncode=0)

            # Act
            result = run(["lsblk", "-J"])

        # Assert
        mock_run.assert_called_once_with(
            ["lsblk", "-J"], text=True, capture_output=True, check=True
        )

    def test_should_raise_on_subprocess_failure(self):
        # Arrange
        with patch("detect.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command failed")

            # Act & Assert
            with pytest.raises(Exception, match="Command failed"):
                run(["lsblk"])


class TestGetLsblk:
    def test_should_parse_lsblk_json_output(self):
        # Arrange
        mock_result = MagicMock()
        mock_result.stdout = '{"blockdevices": [{"name": "sda"}]}'

        with patch("detect.subprocess.run", return_value=mock_result):
            # Act
            result = get_lsblk()

        # Assert
        assert result == {"blockdevices": [{"name": "sda"}]}


class TestToBool:
    def test_should_return_false_for_zero_values(self):
        assert _to_bool(0) is False
        assert _to_bool("0") is False
        assert _to_bool(False) is False

    def test_should_return_true_for_one_values(self):
        assert _to_bool(1) is True
        assert _to_bool("1") is True
        assert _to_bool(True) is True

    def test_should_return_none_for_invalid_values(self):
        assert _to_bool("yes") is None
        assert _to_bool("no") is None
        assert _to_bool("") is None
        assert _to_bool(None) is None
        assert _to_bool(2) is None


class TestFindCandidateDevices:
    def test_should_filter_and_sort_removable_devices(self, monkeypatch, tmp_path):
        # Arrange
        config = Config(
            mount_point=tmp_path / "mount",
            destination_root=tmp_path / "dest",
        )
        lsblk_data = {
            "blockdevices": [
                {
                    "name": "sda",
                    "path": "/dev/sda",
                    "type": "disk",
                    "children": [
                        {
                            "name": "sda1",
                            "path": "/dev/sda1",
                            "type": "part",
                            "fstype": "exfat",
                            "mountpoint": None,
                            "label": "CAMERA",
                            "rm": 1,
                            "size": "64G",
                            "model": "Reader",
                            "tran": "usb",
                        }
                    ],
                },
                {
                    "name": "mmcblk0p1",
                    "path": "/dev/mmcblk0p1",
                    "type": "part",
                    "fstype": "vfat",
                    "mountpoint": None,
                    "label": "CARD",
                    "rm": 1,
                    "size": "32G",
                    "model": None,
                    "tran": "mmc",
                },
                {
                    "name": "nvme0n1p1",
                    "path": "/dev/nvme0n1p1",
                    "type": "part",
                    "fstype": "ext4",
                    "mountpoint": None,
                    "label": "ROOT",
                    "rm": 0,
                    "size": "1T",
                    "model": None,
                    "tran": "nvme",
                },
                {
                    "name": "sdb1",
                    "path": "/dev/sdb1",
                    "type": "part",
                    "fstype": "exfat",
                    "mountpoint": "/media/already-mounted",
                    "label": "USED",
                    "rm": 1,
                    "size": "16G",
                    "model": None,
                    "tran": "usb",
                },
            ]
        }

        monkeypatch.setattr("detect.get_lsblk", lambda: lsblk_data)

        # Act
        candidates = find_candidate_devices(config)

        # Assert
        assert [device.path for device in candidates] == ["/dev/mmcblk0p1", "/dev/sda1"]
        assert candidates[0].label == "CARD"
        assert candidates[1].label == "CAMERA"

    def test_should_respect_supported_filesystems(self, monkeypatch, tmp_path):
        # Arrange
        config = Config(
            mount_point=tmp_path / "mount",
            destination_root=tmp_path / "dest",
            supported_filesystems=("exfat",),
        )
        monkeypatch.setattr(
            "detect.get_lsblk",
            lambda: {
                "blockdevices": [
                    {
                        "name": "mmcblk0p1",
                        "path": "/dev/mmcblk0p1",
                        "type": "part",
                        "fstype": "vfat",
                        "mountpoint": None,
                        "label": "CARD",
                        "rm": 1,
                        "size": "32G",
                        "model": None,
                        "tran": "mmc",
                    }
                ]
            },
        )

        # Act
        candidates = find_candidate_devices(config)

        # Assert
        assert candidates == []


class TestDeviceMatchesPatterns:
    def test_should_return_true_when_pattern_matches(self):
        from detect import _device_matches_patterns

        patterns = [("/dev/sd*", False), ("/dev/mmcblk*", False)]
        assert _device_matches_patterns("/dev/sda1", patterns) is True
        assert _device_matches_patterns("/dev/mmcblk0p1", patterns) is True

    def test_should_return_false_when_excluded_pattern_matches(self):
        from detect import _device_matches_patterns

        patterns = [("/dev/nvme*", True), ("/dev/sd*", False)]
        assert _device_matches_patterns("/dev/nvme0n1p1", patterns) is False

    def test_should_return_false_when_no_pattern_matches(self):
        from detect import _device_matches_patterns

        patterns = [("/dev/sd*", False)]
        assert _device_matches_patterns("/dev/vda1", patterns) is False

    def test_should_respect_pattern_order(self):
        from detect import _device_matches_patterns

        patterns = [("/dev/sd*", True), ("/dev/sdb1", False)]
        assert (
            _device_matches_patterns("/dev/sdb1", patterns) is True
        )  # later pattern wins
        assert (
            _device_matches_patterns("/dev/sda1", patterns) is False
        )  # only matches first


class TestFindCandidateDevicesWithPatterns:
    def test_should_filter_devices_by_patterns(self, monkeypatch, tmp_path):
        # Arrange
        config = Config(
            mount_point=tmp_path / "mount",
            destination_root=tmp_path / "dest",
            device_patterns=[("/dev/sd*", False), ("/dev/mmcblk*", False)],
        )
        lsblk_data = {
            "blockdevices": [
                {
                    "name": "sda",
                    "path": "/dev/sda",
                    "type": "disk",
                    "children": [
                        {
                            "name": "sda1",
                            "path": "/dev/sda1",
                            "type": "part",
                            "fstype": "exfat",
                            "mountpoint": None,
                            "label": "CAMERA",
                            "rm": 1,
                            "size": "64G",
                            "model": None,
                            "tran": "usb",
                        }
                    ],
                },
                {
                    "name": "nvme0n1p1",
                    "path": "/dev/nvme0n1p1",
                    "type": "part",
                    "fstype": "exfat",
                    "mountpoint": None,
                    "label": "SYSTEM",
                    "rm": 0,
                    "size": "256G",
                    "model": None,
                    "tran": "nvme",
                },
            ]
        }
        monkeypatch.setattr("detect.get_lsblk", lambda: lsblk_data)

        # Act
        candidates = find_candidate_devices(config)

        # Assert - only sd* devices should be included, nvme excluded
        assert [device.path for device in candidates] == ["/dev/sda1"]
        assert candidates[0].label == "CAMERA"

    def test_should_exclude_specific_device_with_negation(self, monkeypatch, tmp_path):
        # Arrange
        config = Config(
            mount_point=tmp_path / "mount",
            destination_root=tmp_path / "dest",
            device_patterns=[
                ("/dev/sd*", False),
                ("/dev/sdb1", True),
            ],
        )
        lsblk_data = {
            "blockdevices": [
                {
                    "name": "sda",
                    "path": "/dev/sda",
                    "type": "disk",
                    "children": [
                        {
                            "name": "sda1",
                            "path": "/dev/sda1",
                            "type": "part",
                            "fstype": "vfat",
                            "mountpoint": None,
                            "label": "CARD1",
                            "rm": 1,
                            "size": "32G",
                            "model": None,
                            "tran": "usb",
                        }
                    ],
                },
                {
                    "name": "sdb",
                    "path": "/dev/sdb",
                    "type": "disk",
                    "children": [
                        {
                            "name": "sdb1",
                            "path": "/dev/sdb1",
                            "type": "part",
                            "fstype": "vfat",
                            "mountpoint": None,
                            "label": "CARD2",
                            "rm": 1,
                            "size": "64G",
                            "model": None,
                            "tran": "usb",
                        }
                    ],
                },
            ]
        }
        monkeypatch.setattr("detect.get_lsblk", lambda: lsblk_data)

        # Act
        candidates = find_candidate_devices(config)

        # Assert - only sda1 should be included, sdb1 excluded
        assert [device.path for device in candidates] == ["/dev/sda1"]
