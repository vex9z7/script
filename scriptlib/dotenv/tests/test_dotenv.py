from __future__ import annotations

import os
import tempfile
from pathlib import Path

from scriptlib import dotenv


class TestLoadDotenv:
    def test_read_dotenv_returns_values_without_injecting(self, monkeypatch):
        monkeypatch.delenv("TEST_VAR", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("TEST_VAR=value\n")

            values = dotenv.read_dotenv(env_path)

            assert values == {"TEST_VAR": "value"}
            assert os.environ.get("TEST_VAR") is None

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

    def test_inject_env_can_overwrite_existing(self, monkeypatch):
        monkeypatch.setenv("TEST_VAR", "existing")

        dotenv.inject_env({"TEST_VAR": "updated"}, overwrite=True)

        assert os.environ.get("TEST_VAR") == "updated"
