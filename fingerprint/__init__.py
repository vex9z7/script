import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Fingerprint:
    is_file: bool
    mtime: float | None = None
    ctime: float | None = None
    size: int | None = None
    extension: str | None = None
    get_chunk: Callable[[], bytes | None] = None
    get_sha256: Callable[[], str | None] = None
    file_count: int | None = None
    dir_count: int | None = None


def get_fingerprint(path: Path) -> Fingerprint:
    stat = path.stat()
    _sha256 = None
    _chunk = None

    def compute_sha256() -> str | None:
        nonlocal _sha256
        if _sha256 is None:
            hasher = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            _sha256 = hasher.hexdigest()
        return _sha256

    def read_chunk() -> bytes | None:
        nonlocal _chunk
        if _chunk is None:
            try:
                with open(path, "rb") as f:
                    _chunk = f.read(8192)
            except OSError:
                _chunk = b""
        return _chunk if _chunk else None

    if path.is_file():
        return Fingerprint(
            is_file=True,
            mtime=stat.st_mtime,
            ctime=stat.st_ctime,
            size=stat.st_size,
            extension=path.suffix.lower() or None,
            get_chunk=read_chunk,
            get_sha256=compute_sha256,
        )
    else:
        children = list(path.iterdir())
        return Fingerprint(
            is_file=False,
            mtime=stat.st_mtime,
            ctime=stat.st_ctime,
            file_count=sum(1 for c in children if c.is_file()),
            dir_count=sum(1 for c in children if c.is_dir()),
        )


def fingerprints_match(a: Fingerprint, b: Fingerprint) -> bool:
    if a.mtime != b.mtime:
        return False

    if a.ctime is not None and b.ctime is not None:
        if a.ctime != b.ctime:
            return False

    if a.is_file != b.is_file:
        return False

    if a.is_file:
        if a.extension != b.extension or a.size != b.size:
            return False
    else:
        if a.file_count != b.file_count:
            return False

    if a.get_chunk and b.get_chunk:
        if a.get_chunk() != b.get_chunk():
            return False

    if a.get_sha256 and b.get_sha256:
        if a.get_sha256() != b.get_sha256():
            return False

    return True
