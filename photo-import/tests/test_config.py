from __future__ import annotations

import os
import tempfile
from pathlib import Path

from config import Config

import dotenv


class TestLoadDotenv:
    def test_load_dotenv_reads_file(self, monkeypatch):
        monkeypatch.delenv("PHOTO_IMPORT_LOCK_FILE", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("PHOTO_IMPORT_LOCK_FILE=/custom/lock\n")

            dotenv.load_dotenv(env_path)

            assert os.environ.get("PHOTO_IMPORT_LOCK_FILE") == "/custom/lock"

    def test_load_dotenv_skips_missing_file(self, monkeypatch):
        monkeypatch.delenv("PHOTO_IMPORT_LOCK_FILE", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".nonexistent"
            dotenv.load_dotenv(env_path)

            assert os.environ.get("PHOTO_IMPORT_LOCK_FILE") is None

    def test_load_dotenv_ignores_comments(self, monkeypatch):
        monkeypatch.delenv("PHOTO_IMPORT_LOCK_FILE", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("# comment\nPHOTO_IMPORT_LOCK_FILE=/test\n")

            dotenv.load_dotenv(env_path)

            assert os.environ.get("PHOTO_IMPORT_LOCK_FILE") == "/test"

    def test_load_dotenv_ignores_empty_lines(self, monkeypatch):
        monkeypatch.delenv("PHOTO_IMPORT_LOCK_FILE", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("\n\nPHOTO_IMPORT_LOCK_FILE=/test\n\n")

            dotenv.load_dotenv(env_path)

            assert os.environ.get("PHOTO_IMPORT_LOCK_FILE") == "/test"

    def test_load_dotenv_does_not_override_existing(self, monkeypatch):
        monkeypatch.setenv("PHOTO_IMPORT_LOCK_FILE", "/existing")
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("PHOTO_IMPORT_LOCK_FILE=/from_file\n")

            dotenv.load_dotenv(env_path)

            assert os.environ.get("PHOTO_IMPORT_LOCK_FILE") == "/existing"


class TestConfigDefaults:
    def test_config_has_correct_defaults(self):
        config = Config()

        assert config.lock_file == Path("/tmp/photo-import.lock")
        assert config.mount_point == Path("/mnt/camera-sd-card")
        assert config.destination_root == Path("/mnt/tank/photo/import")
