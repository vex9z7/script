from __future__ import annotations

import json
import logging
import sys
from pathlib import Path


def build_logger(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("photo_import")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def save_state(state_file: Path, state: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
