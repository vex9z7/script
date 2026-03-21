from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from photo_import.detect import CandidateDevice


def make_mock_process_lock():
    class MockFileLock:
        def __init__(self, lock_path):
            self.lock_path = lock_path

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    return MockFileLock


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
