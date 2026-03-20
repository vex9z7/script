from __future__ import annotations

from sync import sync


class TestSync:
    def test_sync_copies_new_files(self, tmp_path):
        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source.mkdir()
        (source / "file.txt").write_text("content")

        stats = sync(source, dest)

        assert stats.copied == 1
        assert stats.skipped == 0
        assert stats.deleted == 0
        assert (dest / "file.txt").read_text() == "content"

    def test_sync_skips_identical_files(self, tmp_path):
        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source.mkdir()
        dest.mkdir()
        (source / "file.txt").write_text("content")
        (dest / "file.txt").write_text("content")

        stats = sync(source, dest)

        assert stats.copied == 0
        assert stats.skipped == 1
        assert stats.deleted == 0

    def test_sync_handles_nested_directories(self, tmp_path):
        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source.mkdir()
        (source / "dir").mkdir()
        (source / "dir" / "file.txt").write_text("content")

        stats = sync(source, dest)

        assert stats.copied == 1
        assert stats.deleted == 0
        assert (dest / "dir" / "file.txt").read_text() == "content"

    def test_sync_respects_filter(self, tmp_path):
        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source.mkdir()
        (source / "keep.txt").write_text("keep")
        (source / "skip.txt").write_text("skip")

        stats = sync(source, dest, filter=lambda f: f.name != "skip.txt")

        assert stats.copied == 1
        assert stats.deleted == 0
        assert (dest / "keep.txt").exists()
        assert not (dest / "skip.txt").exists()

    def test_sync_filters_by_extension(self, tmp_path):
        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source.mkdir()
        (source / "image.jpg").write_text("image")
        (source / "video.mp4").write_text("video")
        (source / "document.txt").write_text("text")

        stats = sync(
            source,
            dest,
            filter=lambda f: f.suffix.lower() in {".jpg", ".mp4"},
        )

        assert stats.copied == 2
        assert stats.deleted == 0
        assert (dest / "image.jpg").exists()
        assert (dest / "video.mp4").exists()
        assert not (dest / "document.txt").exists()

    def test_sync_deletes_extra_files_in_destination(self, tmp_path):
        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source.mkdir()
        dest.mkdir()
        (source / "keep.txt").write_text("keep")
        (dest / "keep.txt").write_text("keep")
        (dest / "delete.txt").write_text("delete")
        import os

        src_stat = os.stat(source / "keep.txt")
        os.utime(dest / "keep.txt", (src_stat.st_atime, src_stat.st_mtime))

        stats = sync(source, dest)

        assert stats.copied == 0
        assert stats.skipped == 1
        assert stats.deleted == 1
        assert (dest / "keep.txt").exists()
        assert not (dest / "delete.txt").exists()

    def test_sync_strict_compares_content_when_fingerprint_matches(self, tmp_path):
        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source.mkdir()
        dest.mkdir()
        (source / "file.txt").write_text("content1")
        (dest / "file.txt").write_text("content2")

        stats = sync(source, dest, strict=True)

        assert stats.copied == 1
        assert stats.skipped == 0
        assert (dest / "file.txt").read_text() == "content1"
