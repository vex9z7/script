from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import log


class TestBuildLogger:
    def test_build_logger_creates_logger(self):
        logger = log.build_logger("test")
        assert logger.name == "test"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1

    def test_build_logger_returns_same_logger(self):
        logger1 = log.build_logger("test_same")
        logger2 = log.build_logger("test_same")
        assert logger1 is logger2

    def test_build_logger_with_custom_level(self):
        logger = log.build_logger("test_level", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_build_logger_writes_to_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = log.build_logger("test_file", log_file=log_path)

            logger.info("test message")

            assert log_path.exists()
            assert "test message" in log_path.read_text()

    def test_build_logger_does_not_propagate(self):
        logger = log.build_logger("test_no_propagate")
        assert logger.propagate is False

    def test_build_logger_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "subdir" / "test.log"
            logger = log.build_logger("test_mkdir", log_file=log_path)

            logger.info("test")

            assert log_path.exists()
