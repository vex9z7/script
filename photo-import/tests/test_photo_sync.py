from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from config import Config
from detect import CandidateDevice
from photo_sync import sync_media, _matches


@pytest.fixture
def candidate_device():
    return CandidateDevice(
        path="/dev/mmcblk0p1",
        fstype="exfat",
        label="CARD",
        size="32G",
        removable=True,
        model=None,
        transport="mmc",
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
            mount_point=mount_point,
            destination_root=destination_root,
        )

        # Act
        stats = sync_media(config, mock_logger, candidate_device)

        # Assert
        assert stats.synced_files == 2
        assert (
            destination_root / "DCIM" / "100CANON" / "image.jpg"
        ).read_text() == "image"
        assert (
            destination_root / "DCIM" / "100CANON" / "video.mp4"
        ).read_text() == "video"

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
            mount_point=mount_point,
            destination_root=destination_root,
            excluded_patterns=[
                ("*.jpg", False),
                ("THUMBNAILS", True),
            ],
        )

        # Act
        stats = sync_media(config, mock_logger, candidate_device)

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
            mount_point=mount_point,
            destination_root=destination_root,
            excluded_patterns=[
                ("*.jpg", False),
                ("*.mp4", False),
                ("*.thm", True),
            ],
        )

        # Act
        stats = sync_media(config, mock_logger, candidate_device)

        # Assert
        assert stats.synced_files == 1  # photo.jpg
        assert stats.filtered_out == 1  # notes.txt (no match)
        # preview.thm is excluded (not counted)

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
            mount_point=mount_point,
            destination_root=destination_root,
        )

        # Act - run twice to trigger skips
        sync_media(config, mock_logger, candidate_device)
        stats = sync_media(config, mock_logger, candidate_device)

        # Assert
        assert stats.synced_files == 0
        assert stats.skipped == 1


class TestMatches:
    def test_should_match_allowed_pattern(self):
        patterns = [("*.jpg", False), ("*.mp4", False)]
        matched, excluded = _matches("photo.jpg", patterns)
        assert matched is True
        assert excluded is False

    def test_should_match_excluded_pattern(self):
        patterns = [("*.jpg", False), ("*.THM", True)]
        matched, excluded = _matches("thumb.THM", patterns)
        assert matched is True
        assert excluded is True

    def test_should_not_match_any_pattern(self):
        patterns = [("*.jpg", False)]
        matched, excluded = _matches("photo.txt", patterns)
        assert matched is False
        assert excluded is False

    def test_should_respect_pattern_order(self):
        patterns = [("*.jpg", False), ("thumb*", True)]
        matched, excluded = _matches("thumb_photo.jpg", patterns)
        assert matched is True
        assert excluded is True
