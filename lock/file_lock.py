import errno
import os
import sys

from . import _native


class ProcessLock:
    def __init__(self, lock_path):
        self.lock_path = lock_path
        self._lock_file = None
        self._acquired = False

    def acquire(self):
        if self._acquired:
            raise LockFailedError("Lock already acquired")
        lock_dir = os.path.dirname(self.lock_path)
        if lock_dir and not os.path.exists(lock_dir):
            os.makedirs(lock_dir, exist_ok=True)

        try:
            self._lock_file = open(self.lock_path, "w")
        except OSError as e:
            if e.errno == errno.ENOENT and lock_dir:
                os.makedirs(lock_dir, exist_ok=True)
                self._lock_file = open(self.lock_path, "w")
            else:
                raise

        try:
            _native.acquire_lock(self._lock_file)
            self._acquired = True
            self._lock_file.write(str(os.getpid()))
            self._lock_file.flush()
            self._lock_file.truncate()
        except OSError as e:
            self._lock_file.close()
            self._lock_file = None
            raise LockFailedError(f"Failed to acquire lock: {e}") from e

    def release(self):
        if self._lock_file is not None:
            try:
                _native.release_lock(self._lock_file)
            finally:
                self._lock_file.close()
                self._lock_file = None
            self._acquired = False

    def is_locked(self):
        if os.path.exists(self.lock_path):
            try:
                with open(self.lock_path) as f:
                    pid_str = f.read().strip()
                    if pid_str:
                        pid = int(pid_str)
                        return is_process_running(pid)
            except (ValueError, OSError):
                pass
        return False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


def is_process_running(pid):
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class LockFailedError(Exception):
    pass


def acquire_lock(lock_path):
    lock = ProcessLock(lock_path)
    lock.acquire()
    return lock


def ensure_locked(lock_path):
    lock = ProcessLock(lock_path)
    if lock.is_locked():
        print(
            f"Error: Another instance is already running. Lock file: {lock_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    lock.acquire()
    return lock
