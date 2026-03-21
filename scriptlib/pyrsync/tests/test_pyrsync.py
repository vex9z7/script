from __future__ import annotations

import os

from scriptlib.pyrsync import sync


class TestSync:
    def test_should_copy_filtered_files_and_delete_extras(self, tmp_path):
        source = tmp_path / "source"
        destination = tmp_path / "dest"
        source_media = source / "DCIM" / "100MSDCF"
        source_media.mkdir(parents=True)
        destination_media = destination / "DCIM" / "100MSDCF"
        destination_media.mkdir(parents=True)

        (source_media / "image.jpg").write_text("image", encoding="utf-8")
        (source_media / "skip.txt").write_text("skip", encoding="utf-8")
        (destination_media / "old.jpg").write_text("old", encoding="utf-8")

        result = sync(
            source=source,
            destination=destination,
            filters=[
                "- THUMBNAILS",
                "- THUMBNAILS/***",
                "+ */",
                "+ *.jpg",
                "- *",
            ],
        )

        assert result.copied == 1
        assert result.deleted >= 1
        assert (destination_media / "image.jpg").read_text(encoding="utf-8") == "image"
        assert not (destination_media / "old.jpg").exists()
        assert not (destination_media / "skip.txt").exists()

    def test_should_preserve_directory_mtime(self, tmp_path):
        source = tmp_path / "source"
        destination = tmp_path / "dest"
        source_dir = source / "DCIM" / "100MSDCF"
        source_dir.mkdir(parents=True)
        (source_dir / "image.jpg").write_text("image", encoding="utf-8")

        source_mtime = 1_700_000_000
        os.utime(source_dir, (source_mtime, source_mtime))

        sync(
            source=source,
            destination=destination,
            filters=["+ */", "+ *.jpg", "- *"],
        )

        destination_dir = destination / "DCIM" / "100MSDCF"
        assert int(destination_dir.stat().st_mtime) == source_mtime

    def test_should_converge_on_second_run(self, tmp_path):
        source = tmp_path / "source"
        destination = tmp_path / "dest"
        source_dir = source / "DCIM" / "100MSDCF"
        source_dir.mkdir(parents=True)
        (source_dir / "image.jpg").write_text("image", encoding="utf-8")

        filters = ["+ */", "+ *.jpg", "- *"]

        first = sync(source=source, destination=destination, filters=filters)
        second = sync(source=source, destination=destination, filters=filters)

        assert first.copied == 1
        assert second.copied == 0
        assert second.deleted == 0
