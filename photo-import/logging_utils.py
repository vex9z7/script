from __future__ import annotations

import logging
import sys


def build_logger() -> logging.Logger:
    logger = logging.getLogger("photo_import")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    return logger
