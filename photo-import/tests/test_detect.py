from __future__ import annotations

from config import Config
from detect import find_candidate_devices


def test_find_candidate_devices_filters_and_sorts(monkeypatch, tmp_path):
    config = Config(
        base_dir=tmp_path / "base",
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

    candidates = find_candidate_devices(config)

    assert [device.path for device in candidates] == ["/dev/mmcblk0p1", "/dev/sda1"]
    assert candidates[0].label == "CARD"
    assert candidates[1].label == "CAMERA"


def test_find_candidate_devices_respects_supported_filesystems(monkeypatch, tmp_path):
    config = Config(
        base_dir=tmp_path / "base",
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

    assert find_candidate_devices(config) == []
