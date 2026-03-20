from __future__ import annotations

import os
import tempfile
from pathlib import Path

import dotenv


class TestLoadDotenv:
    def test_load_dotenv_reads_file(self, monkeypatch):
        monkeypatch.delenv("TEST_VAR", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("TEST_VAR=value\n")

            dotenv.load_dotenv(env_path)

            assert os.environ.get("TEST_VAR") == "value"

    def test_load_dotenv_skips_missing_file(self, monkeypatch):
        monkeypatch.delenv("TEST_VAR", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".nonexistent"

            dotenv.load_dotenv(env_path)

            assert os.environ.get("TEST_VAR") is None

    def test_load_dotenv_ignores_comments(self, monkeypatch):
        monkeypatch.delenv("TEST_VAR", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("# comment\nTEST_VAR=value\n")

            dotenv.load_dotenv(env_path)

            assert os.environ.get("TEST_VAR") == "value"

    def test_load_dotenv_ignores_empty_lines(self, monkeypatch):
        monkeypatch.delenv("TEST_VAR", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("\n\nTEST_VAR=value\n\n")

            dotenv.load_dotenv(env_path)

            assert os.environ.get("TEST_VAR") == "value"

    def test_load_dotenv_does_not_override_existing(self, monkeypatch):
        monkeypatch.setenv("TEST_VAR", "existing")
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("TEST_VAR=from_file\n")

            dotenv.load_dotenv(env_path)

            assert os.environ.get("TEST_VAR") == "existing"
