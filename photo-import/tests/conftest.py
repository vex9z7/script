from __future__ import annotations

import sys
from pathlib import Path

PHOTO_IMPORT_ROOT = Path(__file__).resolve().parents[1]

if str(PHOTO_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOTO_IMPORT_ROOT))
