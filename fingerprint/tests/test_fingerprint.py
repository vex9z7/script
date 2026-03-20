from __future__ import annotations

import pytest

from fingerprint import Fingerprint, fingerprints_match, get_fingerprint


class TestFingerprint:
    def test_get_fingerprint_returns_size_and_mtime(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        fp = get_fingerprint(test_file)

        assert isinstance(fp, Fingerprint)
        assert fp.size == 5
        assert fp.mtime > 0
        assert callable(fp.get_sha256)

    def test_get_fingerprint_sha256_is_memoized(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        fp = get_fingerprint(test_file)

        sha1 = fp.get_sha256()
        sha2 = fp.get_sha256()
        assert sha1 == sha2

    def test_fingerprints_match_same(self):
        fp1 = Fingerprint(size=5, mtime=1000.0, get_sha256=lambda: "abc123")
        fp2 = Fingerprint(size=5, mtime=1000.0, get_sha256=lambda: "abc123")

        assert fingerprints_match(fp1, fp2) is True

    def test_fingerprints_match_different_size(self):
        fp1 = Fingerprint(size=5, mtime=1000.0, get_sha256=lambda: "abc123")
        fp2 = Fingerprint(size=6, mtime=1000.0, get_sha256=lambda: "abc123")

        assert fingerprints_match(fp1, fp2) is False

    def test_fingerprints_match_different_mtime(self):
        fp1 = Fingerprint(size=5, mtime=1000.0, get_sha256=lambda: "abc123")
        fp2 = Fingerprint(size=5, mtime=2000.0, get_sha256=lambda: "abc123")

        assert fingerprints_match(fp1, fp2) is False

    def test_get_fingerprint_on_nonexistent_file(self, tmp_path):
        test_file = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            get_fingerprint(test_file)


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

        def counting_get_sha256():
            call_count[0] += 1
            return original_get_sha256()

        fp1 = Fingerprint(
            size=fp1.size, mtime=fp1.mtime, get_sha256=counting_get_sha256
        )

        fingerprints_match(fp1, fp2)

        assert call_count[0] == 0

    def test_sha256_not_computed_when_mtime_differs(self):
        fp1 = Fingerprint(size=5, mtime=1000.0, get_sha256=lambda: "abc123")
        fp2 = Fingerprint(size=5, mtime=2000.0, get_sha256=lambda: "abc123")

        call_count = [0]

        def counting_get_sha256():
            call_count[0] += 1
            return "abc123"

        fp1 = Fingerprint(
            size=fp1.size, mtime=fp1.mtime, get_sha256=counting_get_sha256
        )

        fingerprints_match(fp1, fp2)

        assert call_count[0] == 0

    def test_sha256_computed_when_size_and_mtime_match(self, tmp_path):
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("hello")
        file2.write_text("hello")

        fp1 = get_fingerprint(file1)
        fp2 = get_fingerprint(file2)

        assert fp1.size == fp2.size
        assert fp1.mtime == fp2.mtime

        sha_called = [False]
        original_get_sha256 = fp1.get_sha256

        def counting_get_sha256():
            sha_called[0] = True
            return original_get_sha256()

        fp1 = Fingerprint(
            size=fp1.size, mtime=fp1.mtime, get_sha256=counting_get_sha256
        )

        fingerprints_match(fp1, fp2)

        assert sha_called[0] is True
