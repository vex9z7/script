from __future__ import annotations

import os

import pytest

from flockplus import ProcessLock


class TestFlockPlus:
    @pytest.fixture
    def lock_path(self, tmp_path):
        return str(tmp_path / "test.lock")

    def test_should_create_lock_file(self, lock_path):
        with ProcessLock(lock_path):
            assert os.path.exists(lock_path)

    def test_should_block_concurrent_access(self, lock_path):
        with ProcessLock(lock_path):
            with pytest.raises(OSError):
                ProcessLock(lock_path).__enter__()

    def test_should_allow_reuse_after_release(self, lock_path):
        with ProcessLock(lock_path):
            pass
        with ProcessLock(lock_path):
            pass
