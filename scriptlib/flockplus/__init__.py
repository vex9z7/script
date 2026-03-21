import fcntl
import os


class FileLock:
    """File-based lock using fcntl.flock().

    Usage:
        with FileLock("/tmp/app.lock"):
            # work
    """

    def __init__(self, lock_path):
        self.lock_path = lock_path
        self._file = None

    def __enter__(self):
        lock_dir = os.path.dirname(self.lock_path)
        if lock_dir:
            os.makedirs(lock_dir, exist_ok=True)
        self._file = open(self.lock_path, "w", encoding="utf-8")
        fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        self._file.write(str(os.getpid()))
        return self

    def __exit__(self, *args):
        assert self._file is not None
        fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        self._file.close()


__all__ = ["FileLock"]
