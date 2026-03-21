from __future__ import annotations

import os

import pytest

from flockplus import FileLock


class TestFlockPlus:
    @pytest.fixture
    def lock_path(self, tmp_path):
        return str(tmp_path / "test.lock")

    def test_should_create_lock_file(self, lock_path):
        with FileLock(lock_path):
            assert os.path.exists(lock_path)

    def test_should_block_concurrent_access(self, lock_path):
        with FileLock(lock_path):
            with pytest.raises(OSError):
                FileLock(lock_path).__enter__()

    def test_should_allow_reuse_after_release(self, lock_path):
        with FileLock(lock_path):
            pass
        with FileLock(lock_path):
            pass
