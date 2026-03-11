from __future__ import annotations

import logging

import pytest
from config import Config
from detect import CandidateDevice
from photo_copy import copy_media_files


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


def test_copy_media_files_copies_allowed_media_and_skips_excluded_items(
    tmp_path, candidate_device
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
        base_dir=tmp_path / "base",
        mount_point=mount_point,
        destination_root=destination_root,
        excluded_dir_names=frozenset({"thumbnails"}),
    )

    stats = copy_media_files(config, logging.getLogger("test"), candidate_device)

    assert stats.copied_files == 2
    assert stats.filtered_out == 2
    assert stats.skipped_existing == 0
    assert (destination_root / "DCIM" / "100CANON" / "image.JPG").read_text() == "image"
    assert (destination_root / "DCIM" / "100CANON" / "video.MP4").read_text() == "video"
    assert not (destination_root / "THUMBNAILS" / "skip.jpg").exists()


def test_copy_media_files_skips_existing_files_by_default(tmp_path, candidate_device):
    mount_point = tmp_path / "mount"
    destination_root = tmp_path / "dest"
    source_dir = mount_point / "DCIM"
    source_dir.mkdir(parents=True)
    source_file = source_dir / "image.jpg"
    source_file.write_text("new", encoding="utf-8")

    existing_destination = destination_root / "DCIM" / "image.jpg"
    existing_destination.parent.mkdir(parents=True)
    existing_destination.write_text("old", encoding="utf-8")

    config = Config(
        base_dir=tmp_path / "base",
        mount_point=mount_point,
        destination_root=destination_root,
    )

    stats = copy_media_files(config, logging.getLogger("test"), candidate_device)

    assert stats.copied_files == 0
    assert stats.skipped_existing == 1
    assert existing_destination.read_text(encoding="utf-8") == "old"
