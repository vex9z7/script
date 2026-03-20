from __future__ import annotations

import sys
from pathlib import Path

import pytest

PHOTO_IMPORT_ROOT = Path(__file__).resolve().parents[1]

if str(PHOTO_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOTO_IMPORT_ROOT))

from detect import CandidateDevice

from lock import LockError


def make_mock_process_lock():
    class MockProcessLock:
        def __init__(self, lock_path):
            self.lock_path = lock_path

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    return MockProcessLock


def make_busy_lock():
    class BusyLock:
        def __init__(self, lock_path):
            pass

        def __enter__(self):
            raise LockError("busy")

        def __exit__(self, *args):
            pass

    return BusyLock


@pytest.fixture
def candidate_device():
    return CandidateDevice(
        path="/dev/mmcblk0p1",
        fstype="exfat",
        label="CARD",
        size="32G",
        removable=True,
        model=None,
        transport="mmc",
    )
