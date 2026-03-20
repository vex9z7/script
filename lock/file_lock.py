import fcntl
import os
import sys


class ProcessLock:
    def __init__(self, lock_path):
        self.lock_path = lock_path
        self._lock_file = None
        self._acquired = False

    def acquire(self):
        if self._acquired:
            raise RuntimeError("Lock already acquired")
        if lock_dir := os.path.dirname(self.lock_path):
            os.makedirs(lock_dir, exist_ok=True)
        self._lock_file = open(self.lock_path, "w")
        try:
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._acquired = True
            self._lock_file.write(str(os.getpid()))
            self._lock_file.flush()
        except OSError:
            self._lock_file.close()
            raise

    def release(self):
        if self._lock_file:
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
            self._lock_file.close()
            self._lock_file = None
            self._acquired = False

    def is_locked(self):
        if not os.path.exists(self.lock_path):
            return False
        try:
            pid = int(open(self.lock_path).read().strip())
            os.kill(pid, 0)
            return True
        except (ValueError, OSError):
            return False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()


def ensure_locked(lock_path):
    lock = ProcessLock(lock_path)
    if lock.is_locked():
        print(f"Error: Another instance is running. Lock: {lock_path}", file=sys.stderr)
        sys.exit(1)
    lock.acquire()
    return lock
