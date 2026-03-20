from __future__ import annotations

import os
import tempfile

import pytest

from lock import ProcessLock


class TestProcessLock:
    @pytest.fixture
    def lock_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield os.path.join(tmpdir, "test.lock")

    def test_acquire_and_release_lock(self, lock_path):
        lock = ProcessLock(lock_path)
        assert not os.path.exists(lock_path)
        lock.acquire()
        assert os.path.exists(lock_path)
        lock.release()

    def test_context_manager(self, lock_path):
        with ProcessLock(lock_path) as lock:
            assert lock._acquired is True
            with open(lock_path) as f:
                assert f.read().strip() == str(os.getpid())
        assert lock._acquired is False

    def test_lock_file_contains_pid(self, lock_path):
        lock = ProcessLock(lock_path)
        lock.acquire()
        with open(lock_path) as f:
            content = f.read().strip()
        lock.release()
        assert content == str(os.getpid())

    def test_is_locked_returns_true_when_locked(self, lock_path):
        lock = ProcessLock(lock_path)
        lock.acquire()
        assert lock.is_locked() is True
        lock.release()

    def test_is_locked_returns_false_when_not_locked(self, lock_path):
        lock = ProcessLock(lock_path)
        assert lock.is_locked() is False

    def test_multiple_locks_same_path_fails(self, lock_path):
        lock1 = ProcessLock(lock_path)
        lock1.acquire()
        lock2 = ProcessLock(lock_path)
        with pytest.raises(OSError):
            lock2.acquire()
        lock1.release()

    def test_nested_lock_acquisition(self, lock_path):
        lock = ProcessLock(lock_path)
        lock.acquire()
        try:
            lock.acquire()
            pytest.fail("Should not allow double acquisition")
        except RuntimeError:
            pass
        finally:
            lock.release()
