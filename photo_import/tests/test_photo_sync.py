from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from photo_import.config import Config
from photo_import.detect import CandidateDevice
from photo_import.photo_sync import _rsync_filters, sync_media


@pytest.fixture
def candidate_device():
    return CandidateDevice(
        path="/dev/mmcblk0p1",
        fstype="exfat",
        label="CARD",
        uuid="FA86-7EB0",
        partuuid="part-001",
        size="32G",
        removable=True,
        model="SD Reader",
        serial="CARD123",
        transport="mmc",
        mountpoint=None,
        device_id="sd_reader-card123-exfat-fa86-7eb0-part-001",
    )


@pytest.fixture
def mock_logger():
    return MagicMock()


class TestSyncMedia:
    def test_should_copy_allowed_media_files(
        self, tmp_path, candidate_device, mock_logger
    ):
        # Arrange
        mount_point = tmp_path / "mount"
        destination_root = tmp_path / "dest"
        dcim_dir = mount_point / "DCIM" / "100CANON"
        dcim_dir.mkdir(parents=True)
        (dcim_dir / "image.jpg").write_text("image", encoding="utf-8")
        (dcim_dir / "video.mp4").write_text("video", encoding="utf-8")

        config = Config(
            mount_root=tmp_path / "mount-root",
            import_root=tmp_path / "import-root",
        )

        # Act
        stats = sync_media(
            config, mock_logger, candidate_device, mount_point, destination_root
        )

        # Assert
        assert stats.synced_files == 2
        assert (
            destination_root / "DCIM" / "100CANON" / "image.jpg"
        ).read_text() == "image"
        assert (
            destination_root / "DCIM" / "100CANON" / "video.mp4"
        ).read_text() == "video"
        mock_logger.debug.assert_any_call(
            "starting sync from %s to %s for %s",
            mount_point,
            destination_root,
            candidate_device.path,
        )
        mock_logger.debug.assert_any_call(
            "sync complete for %s: copied=%s skipped=%s filtered_out=%s",
            candidate_device.path,
            2,
            0,
            0,
        )

    def test_should_skip_excluded_directories(
        self, tmp_path, candidate_device, mock_logger
    ):
        # Arrange
        mount_point = tmp_path / "mount"
        destination_root = tmp_path / "dest"
        dcim_dir = mount_point / "DCIM"
        thumbnail_dir = mount_point / "THUMBNAILS"
        dcim_dir.mkdir(parents=True)
        thumbnail_dir.mkdir(parents=True)
        (dcim_dir / "photo.jpg").write_text("photo")
        (thumbnail_dir / "skip.jpg").write_text("skip")

        config = Config(
            mount_root=tmp_path / "mount-root",
            import_root=tmp_path / "import-root",
            excluded_patterns=[
                ("*.jpg", False),
                ("THUMBNAILS", True),
            ],
        )

        # Act
        stats = sync_media(
            config, mock_logger, candidate_device, mount_point, destination_root
        )

        # Assert
        assert stats.synced_files == 1
        assert not (destination_root / "THUMBNAILS" / "skip.jpg").exists()

    def test_should_filter_files_by_extension(
        self, tmp_path, candidate_device, mock_logger
    ):
        # Arrange
        mount_point = tmp_path / "mount"
        destination_root = tmp_path / "dest"
        dcim_dir = mount_point / "DCIM"
        dcim_dir.mkdir(parents=True)
        (dcim_dir / "photo.jpg").write_text("photo")
        (dcim_dir / "notes.txt").write_text("notes")
        (dcim_dir / "preview.thm").write_text("preview")

        config = Config(
            mount_root=tmp_path / "mount-root",
            import_root=tmp_path / "import-root",
            excluded_patterns=[
                ("*.jpg", False),
                ("*.mp4", False),
                ("*.thm", True),
            ],
        )

        # Act
        stats = sync_media(
            config, mock_logger, candidate_device, mount_point, destination_root
        )

        # Assert
        assert stats.synced_files == 1  # photo.jpg
        assert stats.filtered_out == 1  # notes.txt (no match)
        # preview.thm is excluded (not counted)

    def test_should_match_explicit_uppercase_patterns(
        self, tmp_path, candidate_device, mock_logger
    ):
        mount_point = tmp_path / "mount"
        destination_root = tmp_path / "dest"
        dcim_dir = mount_point / "DCIM" / "100MSDCF"
        dcim_dir.mkdir(parents=True)
        (dcim_dir / "DSC00982.JPG").write_text("image")
        (dcim_dir / "DSC00982.THM").write_text("thumb")

        config = Config(
            mount_root=tmp_path / "mount-root",
            import_root=tmp_path / "import-root",
            excluded_patterns=[
                ("*.jpg", False),
                ("*.JPG", False),
                ("*.thm", True),
                ("*.THM", True),
            ],
        )

        stats = sync_media(
            config, mock_logger, candidate_device, mount_point, destination_root
        )

        assert stats.synced_files == 1
        assert (destination_root / "DCIM" / "100MSDCF" / "DSC00982.JPG").exists()
        assert not (destination_root / "DCIM" / "100MSDCF" / "DSC00982.THM").exists()

    def test_should_report_skipped_when_sync_skips(
        self, tmp_path, candidate_device, mock_logger
    ):
        # Arrange
        mount_point = tmp_path / "mount"
        destination_root = tmp_path / "dest"
        dcim_dir = mount_point / "DCIM"
        dcim_dir.mkdir(parents=True)
        (dcim_dir / "existing.jpg").write_text("existing")

        config = Config(
            mount_root=tmp_path / "mount-root",
            import_root=tmp_path / "import-root",
        )

        with patch("photo_import.photo_sync.sync") as mock_sync:
            mock_sync.return_value.copied = 0
            mock_sync.return_value.skipped = 1
            mock_sync.return_value.deleted = 0

            # Act
            stats = sync_media(
                config, mock_logger, candidate_device, mount_point, destination_root
            )

        # Assert
        assert stats.synced_files == 0
        assert stats.skipped == 1


class TestRsyncFilters:
    def test_should_generate_rsync_rules_for_media_subset(self):
        patterns = [
            ("*.jpg", False),
            ("*.JPG", False),
            ("*.thm", True),
            ("THUMBNAILS", True),
        ]

        rules = _rsync_filters(patterns)

        assert rules == [
            "- *.thm",
            "- *.thm/***",
            "- THUMBNAILS",
            "- THUMBNAILS/***",
            "+ */",
            "+ *.jpg",
            "+ *.JPG",
            "- *",
        ]
