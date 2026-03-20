from __future__ import annotations

import os

import pytest

from lock import LockError, ProcessLock


class TestProcessLock:
    @pytest.fixture
    def lock_path(self, tmp_path):
        return tmp_path / "test.lock"

    def test_acquire_and_release_lock(self, lock_path):
        lock = ProcessLock(str(lock_path))
        assert not lock_path.exists()
        lock.acquire()
        assert lock_path.exists()
        lock.release()

    def test_context_manager(self, lock_path):
        with ProcessLock(str(lock_path)) as lock:
            assert lock._acquired is True
            assert lock_path.read_text().strip() == str(os.getpid())
        assert lock._acquired is False

    def test_lock_file_contains_pid(self, lock_path):
        lock = ProcessLock(str(lock_path))
        lock.acquire()
        content = lock_path.read_text().strip()
        lock.release()
        assert content == str(os.getpid())

    def test_is_locked_returns_true_when_locked(self, lock_path):
        lock = ProcessLock(str(lock_path))
        lock.acquire()
        assert lock.is_locked() is True
        lock.release()

    def test_is_locked_returns_false_when_not_locked(self, lock_path):
        lock = ProcessLock(str(lock_path))
        assert lock.is_locked() is False

    def test_acquire_raises_lock_error_when_already_locked(self, lock_path):
        lock1 = ProcessLock(str(lock_path))
        lock1.acquire()
        lock2 = ProcessLock(str(lock_path))
        with pytest.raises(LockError):
            lock2.acquire()
        lock1.release()

    def test_nested_lock_acquisition(self, lock_path):
        lock = ProcessLock(str(lock_path))
        lock.acquire()
        try:
            lock.acquire()
            pytest.fail("Should not allow double acquisition")
        except RuntimeError:
            pass
        finally:
            lock.release()
