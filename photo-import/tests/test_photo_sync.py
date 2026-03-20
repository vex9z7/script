from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest
from config import Config
from detect import CandidateDevice
from photo_sync import sync_media


@dataclass(frozen=True)
class MockSyncResult:
    copied: int = 0
    skipped: int = 0


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


def test_sync_media_copies_allowed_media_and_skips_excluded_items(
    tmp_path, candidate_device, mock_logger
):
    mount_point = tmp_path / "mount"
    destination_root = tmp_path / "dest"
    dcim_dir = mount_point / "DCIM" / "100CANON"
    thumbnail_dir = mount_point / "THUMBNAILS"

    dcim_dir.mkdir(parents=True)
    thumbnail_dir.mkdir(parents=True)
    (dcim_dir / "image.JPG").write_text("image", encoding="utf-8")
    (dcim_dir / "video.MP4").write_text("video", encoding="utf-8")
    (dcim_dir / "preview.THM").write_text("thumbnail", encoding="utf-8")
    (dcim_dir / "notes.txt").write_text("ignore", encoding="utf-8")
    (thumbnail_dir / "skip.jpg").write_text("skip", encoding="utf-8")

    config = Config(
        mount_point=mount_point,
        destination_root=destination_root,
        excluded_dir_names=frozenset({"thumbnails"}),
    )

    stats = sync_media(config, mock_logger, candidate_device)

    assert stats.synced_files == 2
    assert stats.filtered_out == 1
    assert stats.skipped == 0
    assert (destination_root / "DCIM" / "100CANON" / "image.JPG").read_text() == "image"
    assert (destination_root / "DCIM" / "100CANON" / "video.MP4").read_text() == "video"
    assert not (destination_root / "THUMBNAILS" / "skip.jpg").exists()


def test_sync_media_reports_skipped_when_sync_skips(
    monkeypatch, tmp_path, candidate_device, mock_logger
):
    monkeypatch.setattr("photo_sync._has_required_layout", lambda *_: True)

    mock_sync_result = MagicMock()
    mock_sync_result.copied = 0
    mock_sync_result.skipped = 3

    with patch("photo_sync.sync", return_value=mock_sync_result):
        config = Config(
            mount_point=tmp_path / "mount",
            destination_root=tmp_path / "dest",
        )
        stats = sync_media(config, mock_logger, candidate_device)

    assert stats.synced_files == 0
    assert stats.skipped == 3
