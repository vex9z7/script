from __future__ import annotations

from unittest.mock import patch, MagicMock

from photo_import.config import Config
from photo_import.detect import find_candidate_devices, get_lsblk


class TestGetLsblk:
    def test_should_parse_lsblk_json_output(self):
        # Arrange
        mock_result = MagicMock()
        mock_result.stdout = '{"blockdevices": [{"name": "sda"}]}'

        with patch("photo_import.detect.subprocess.run", return_value=mock_result):
            # Act
            result = get_lsblk()

        # Assert
        assert result == {"blockdevices": [{"name": "sda"}]}


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

        monkeypatch.setattr("photo_import.detect.get_lsblk", lambda: lsblk_data)

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
            "photo_import.detect.get_lsblk",
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
        assert not candidates

    def test_should_log_rejection_reasons_when_logger_provided(
        self, monkeypatch, tmp_path
    ):
        config = Config(
            mount_point=tmp_path / "mount",
            destination_root=tmp_path / "dest",
        )
        logger = MagicMock()
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
                            "fstype": "ext4",
                            "mountpoint": None,
                            "label": "SYSTEM",
                            "rm": 1,
                            "size": "64G",
                            "model": None,
                            "tran": "usb",
                        }
                    ],
                }
            ]
        }

        monkeypatch.setattr("photo_import.detect.get_lsblk", lambda: lsblk_data)

        candidates = find_candidate_devices(config, logger=logger)

        assert not candidates
        logger.debug.assert_any_call(
            "device %s %s", "/dev/sda", "rejected: type=disk, expected part"
        )
        logger.debug.assert_any_call(
            "device %s %s", "/dev/sda1", "rejected: unsupported filesystem ext4"
        )

    def test_should_log_acceptance_reason_when_candidate_selected(
        self, monkeypatch, tmp_path
    ):
        config = Config(
            mount_point=tmp_path / "mount",
            destination_root=tmp_path / "dest",
        )
        logger = MagicMock()
        lsblk_data = {
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
        }

        monkeypatch.setattr("photo_import.detect.get_lsblk", lambda: lsblk_data)

        candidates = find_candidate_devices(config, logger=logger)

        assert [device.path for device in candidates] == ["/dev/mmcblk0p1"]
        logger.debug.assert_called_with(
            "device %s %s",
            "/dev/mmcblk0p1",
            "accepted: fstype=vfat, label=CARD, rm=1, tran=mmc",
        )

    def test_should_accept_partition_when_parent_transport_is_usb(
        self, monkeypatch, tmp_path
    ):
        config = Config(
            mount_point=tmp_path / "mount",
            destination_root=tmp_path / "dest",
        )
        lsblk_data = {
            "blockdevices": [
                {
                    "name": "sde",
                    "path": "/dev/sde",
                    "type": "disk",
                    "rm": 1,
                    "tran": "usb",
                    "children": [
                        {
                            "name": "sde1",
                            "path": "/dev/sde1",
                            "type": "part",
                            "fstype": "exfat",
                            "mountpoint": None,
                            "label": "SD_Card",
                            "rm": 1,
                            "size": "64G",
                            "model": None,
                            "tran": None,
                        }
                    ],
                }
            ]
        }

        monkeypatch.setattr("photo_import.detect.get_lsblk", lambda: lsblk_data)

        candidates = find_candidate_devices(config)

        assert [device.path for device in candidates] == ["/dev/sde1"]

    def test_should_reject_partition_when_parent_transport_is_unsupported(
        self, monkeypatch, tmp_path
    ):
        config = Config(
            mount_point=tmp_path / "mount",
            destination_root=tmp_path / "dest",
        )
        lsblk_data = {
            "blockdevices": [
                {
                    "name": "nvme0n1",
                    "path": "/dev/nvme0n1",
                    "type": "disk",
                    "rm": 1,
                    "tran": "nvme",
                    "children": [
                        {
                            "name": "nvme0n1p1",
                            "path": "/dev/nvme0n1p1",
                            "type": "part",
                            "fstype": "exfat",
                            "mountpoint": None,
                            "label": "MAYBE_CARD",
                            "rm": 1,
                            "size": "64G",
                            "model": None,
                            "tran": None,
                        }
                    ],
                }
            ]
        }

        monkeypatch.setattr("photo_import.detect.get_lsblk", lambda: lsblk_data)

        candidates = find_candidate_devices(config)

        assert not candidates


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
        monkeypatch.setattr("photo_import.detect.get_lsblk", lambda: lsblk_data)

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
        monkeypatch.setattr("photo_import.detect.get_lsblk", lambda: lsblk_data)

        # Act
        candidates = find_candidate_devices(config)

        # Assert - only sda1 should be included, sdb1 excluded
        assert [device.path for device in candidates] == ["/dev/sda1"]
