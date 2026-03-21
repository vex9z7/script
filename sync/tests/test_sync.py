from __future__ import annotations

from unittest.mock import patch

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
        from fingerprint import Fingerprint

        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source.mkdir()
        dest.mkdir()
        (source / "file.txt").write_text("content")
        (dest / "file.txt").write_text("content")

        def mock_get_fingerprint(path):
            return Fingerprint(
                is_file=True,
                mtime=1000.0,
                ctime=1001.0,
                size=7,
                extension=".txt",
                get_sha256=lambda: "shared-hash",
            )

        with patch("sync.get_fingerprint", side_effect=mock_get_fingerprint):
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
        from fingerprint import Fingerprint

        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source.mkdir()
        dest.mkdir()
        (source / "keep.txt").write_text("keep")
        (dest / "keep.txt").write_text("keep")
        (dest / "delete.txt").write_text("delete")

        same_mtime = 1000.0

        def mock_get_fingerprint(path):
            return Fingerprint(
                is_file=True,
                mtime=same_mtime,
                size=4,
                extension=".txt",
                get_sha256=lambda: "abc123",
            )

        with patch("sync.get_fingerprint", side_effect=mock_get_fingerprint):
            stats = sync(source, dest)

        assert stats.copied == 0
        assert stats.skipped == 1
        assert stats.deleted == 1
        assert (dest / "keep.txt").exists()
        assert not (dest / "delete.txt").exists()

    def test_sync_strict_compares_content_when_fingerprint_matches(self, tmp_path):
        from fingerprint import Fingerprint

        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source.mkdir()
        dest.mkdir()
        (source / "file.txt").write_text("content1")
        (dest / "file.txt").write_text("content2")

        def mock_get_fingerprint(path):
            return Fingerprint(
                is_file=True,
                mtime=1000.0,
                ctime=1001.0,
                size=8,
                extension=".txt",
                get_sha256=lambda: "shared-hash",
            )

        with patch("sync.get_fingerprint", side_effect=mock_get_fingerprint):
            stats = sync(source, dest, strict=True)

        assert stats.copied == 1
        assert stats.skipped == 0
        assert (dest / "file.txt").read_text() == "content1"

    def test_sync_non_strict_skips_when_fingerprint_matches(self, tmp_path):
        from fingerprint import Fingerprint

        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source.mkdir()
        dest.mkdir()
        (source / "file.txt").write_text("content1")
        (dest / "file.txt").write_text("content2")

        def mock_get_fingerprint(path):
            return Fingerprint(
                is_file=True,
                mtime=1000.0,
                ctime=1001.0,
                size=8,
                extension=".txt",
                get_sha256=lambda: "shared-hash",
            )

        with patch("sync.get_fingerprint", side_effect=mock_get_fingerprint):
            stats = sync(source, dest, strict=False)

        assert stats.copied == 0
        assert stats.skipped == 1
        assert (dest / "file.txt").read_text() == "content2"

    def test_sync_strict_skips_when_file_content_matches(self, tmp_path):
        from fingerprint import Fingerprint

        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source.mkdir()
        dest.mkdir()
        (source / "file.txt").write_text("content")
        (dest / "file.txt").write_text("content")

        def mock_get_fingerprint(path):
            return Fingerprint(
                is_file=True,
                mtime=1000.0,
                ctime=1001.0,
                size=7,
                extension=".txt",
                get_sha256=lambda: "shared-hash",
            )

        with patch("sync.get_fingerprint", side_effect=mock_get_fingerprint):
            stats = sync(source, dest, strict=True)

        assert stats.copied == 0
        assert stats.skipped == 1

    def test_sync_strict_checks_nested_files_recursively(self, tmp_path):
        from fingerprint import Fingerprint

        source = tmp_path / "source"
        dest = tmp_path / "dest"
        source_nested = source / "nested"
        dest_nested = dest / "nested"
        source_nested.mkdir(parents=True)
        dest_nested.mkdir(parents=True)
        (source_nested / "file.txt").write_text("source-content")
        (dest_nested / "file.txt").write_text("dest-content")

        def mock_get_fingerprint(path):
            return Fingerprint(
                is_file=True,
                mtime=1000.0,
                ctime=1001.0,
                size=12,
                extension=".txt",
                get_sha256=lambda: "shared-hash",
            )

        with patch("sync.get_fingerprint", side_effect=mock_get_fingerprint):
            stats = sync(source, dest, strict=True)

        assert stats.copied == 1
        assert stats.skipped == 0
        assert (dest_nested / "file.txt").read_text() == "source-content"
