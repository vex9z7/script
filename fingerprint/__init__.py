import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Fingerprint:
    size: int
    mtime: float
    get_sha256: Callable[[], str]


def get_fingerprint(path: Path) -> Fingerprint:
    stat = path.stat()
    _sha256 = None

    def compute_sha256() -> str:
        nonlocal _sha256
        if _sha256 is None:
            hasher = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            _sha256 = hasher.hexdigest()
        return _sha256

    return Fingerprint(
        size=stat.st_size, mtime=stat.st_mtime, get_sha256=compute_sha256
    )


def fingerprints_match(a: Fingerprint, b: Fingerprint) -> bool:
    if a.size != b.size or a.mtime != b.mtime:
        return False
    return a.get_sha256() == b.get_sha256()
