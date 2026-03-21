from __future__ import annotations

import pytest

from scriptlib.fingerprint import Fingerprint, fingerprints_match, get_fingerprint


class TestFingerprint:
    def test_get_fingerprint_returns_size_and_mtime(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        fp = get_fingerprint(test_file)

        assert isinstance(fp, Fingerprint)
        assert fp.is_file is True
        assert fp.size == 5
        assert fp.mtime is not None and fp.mtime > 0
        assert callable(fp.get_sha256)

    def test_get_fingerprint_sha256_is_memoized(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        fp = get_fingerprint(test_file)

        assert fp.get_sha256 is not None
        sha1 = fp.get_sha256()
        sha2 = fp.get_sha256()
        assert sha1 == sha2

    def test_fingerprints_match_same(self):
        fp1 = Fingerprint(
            is_file=True,
            mtime=1000.0,
            size=5,
            get_sha256=lambda: "abc123",
        )
        fp2 = Fingerprint(
            is_file=True,
            mtime=1000.0,
            size=5,
            get_sha256=lambda: "abc123",
        )

        assert fingerprints_match(fp1, fp2) is True

    def test_fingerprints_match_different_size(self):
        fp1 = Fingerprint(
            is_file=True,
            mtime=1000.0,
            size=5,
            get_sha256=lambda: "abc123",
        )
        fp2 = Fingerprint(
            is_file=True,
            mtime=1000.0,
            size=6,
            get_sha256=lambda: "abc123",
        )

        assert fingerprints_match(fp1, fp2) is False

    def test_fingerprints_match_different_mtime(self):
        fp1 = Fingerprint(
            is_file=True,
            mtime=1000.0,
            size=5,
            get_sha256=lambda: "abc123",
        )
        fp2 = Fingerprint(
            is_file=True,
            mtime=2000.0,
            size=5,
            get_sha256=lambda: "abc123",
        )

        assert fingerprints_match(fp1, fp2) is False

    def test_fingerprints_match_different_extension(self):
        fp1 = Fingerprint(
            is_file=True,
            mtime=1000.0,
            size=5,
            extension=".jpg",
            get_sha256=lambda: "abc123",
        )
        fp2 = Fingerprint(
            is_file=True,
            mtime=1000.0,
            size=5,
            extension=".png",
            get_sha256=lambda: "abc123",
        )

        assert fingerprints_match(fp1, fp2) is False

    def test_fingerprints_match_different_type(self):
        fp1 = Fingerprint(is_file=True, mtime=1000.0, size=5)
        fp2 = Fingerprint(is_file=False, mtime=1000.0)

        assert fingerprints_match(fp1, fp2) is False

    def test_get_fingerprint_on_nonexistent_file(self, tmp_path):
        test_file = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            get_fingerprint(test_file)

    def test_get_fingerprint_on_directory(self, tmp_path):
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("hello")

        fp = get_fingerprint(test_dir)

        assert fp.is_file is False
        assert fp.mtime is not None and fp.mtime > 0
        assert fp.size is None
        assert fp.file_count == 1
        assert fp.dir_count == 0

    def test_fingerprints_match_same_directory(self):
        fp1 = Fingerprint(is_file=False, mtime=1000.0, file_count=5)
        fp2 = Fingerprint(is_file=False, mtime=1000.0, file_count=5)

        assert fingerprints_match(fp1, fp2) is True


class TestFingerprintPerformance:
    def test_sha256_not_computed_when_size_differs(self, tmp_path):
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("hello")
        file2.write_text("hello world")

        fp1 = get_fingerprint(file1)
        fp2 = get_fingerprint(file2)

        call_count = [0]
        original_get_sha256 = fp1.get_sha256
        assert original_get_sha256 is not None

        def counting_get_sha256():
            call_count[0] += 1
            return original_get_sha256()

        fp1 = Fingerprint(
            is_file=True,
            mtime=fp1.mtime,
            size=fp1.size,
            get_sha256=counting_get_sha256,
        )

        fingerprints_match(fp1, fp2)

        assert call_count[0] == 0

    def test_sha256_not_computed_when_mtime_differs(self):
        fp1 = Fingerprint(
            is_file=True,
            mtime=1000.0,
            size=5,
            get_sha256=lambda: "abc123",
        )
        fp2 = Fingerprint(
            is_file=True,
            mtime=2000.0,
            size=5,
            get_sha256=lambda: "abc123",
        )

        call_count = [0]

        def counting_get_sha256():
            call_count[0] += 1
            return "abc123"

        fp1 = Fingerprint(
            is_file=True,
            mtime=fp1.mtime,
            size=fp1.size,
            get_sha256=counting_get_sha256,
        )

        fingerprints_match(fp1, fp2)

        assert call_count[0] == 0

    def test_sha256_computed_when_chunk_matches(self, tmp_path):
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_bytes(b"hello")
        file2.write_bytes(b"hello")

        fp1 = get_fingerprint(file1)
        fp2 = get_fingerprint(file2)

        sha_called = [False]
        original_get_sha256 = fp1.get_sha256
        assert original_get_sha256 is not None

        def counting_get_sha256():
            sha_called[0] = True
            return original_get_sha256()

        fp1 = Fingerprint(
            is_file=True,
            mtime=1000.0,
            ctime=1001.0,
            size=fp1.size,
            extension=fp1.extension,
            get_chunk=fp1.get_chunk,
            get_sha256=counting_get_sha256,
        )
        fp2 = Fingerprint(
            is_file=True,
            mtime=1000.0,
            ctime=1001.0,
            size=fp2.size,
            extension=fp2.extension,
            get_chunk=fp2.get_chunk,
            get_sha256=fp2.get_sha256,
        )

        fingerprints_match(fp1, fp2)

        assert sha_called[0] is True

    def test_chunk_not_computed_when_extension_differs(self, tmp_path):
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.jpg"
        file1.write_bytes(b"hello")
        file2.write_bytes(b"hello")

        fp1 = get_fingerprint(file1)
        fp2 = get_fingerprint(file2)

        call_count = [0]
        original_get_chunk = fp1.get_chunk
        assert original_get_chunk is not None

        def counting_get_chunk():
            call_count[0] += 1
            return original_get_chunk()

        fp1 = Fingerprint(
            is_file=True,
            mtime=fp1.mtime,
            size=fp1.size,
            extension=fp1.extension,
            get_chunk=counting_get_chunk,
        )

        fingerprints_match(fp1, fp2)

        assert call_count[0] == 0
