from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from photo_import.config import Config, ConfigurationError, load_config

from scriptlib import dotenv


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
        assert config.mount_point is None
        assert config.destination_root is None


class TestLoadConfig:
    def test_load_config_raises_when_mount_point_missing(self, monkeypatch):
        monkeypatch.delenv("PHOTO_IMPORT_MOUNT_POINT", raising=False)
        monkeypatch.delenv("PHOTO_IMPORT_DESTINATION_ROOT", raising=False)
        monkeypatch.setenv("PHOTO_IMPORT_DESTINATION_ROOT", "/dest")

        with pytest.raises(ConfigurationError, match="PHOTO_IMPORT_MOUNT_POINT"):
            load_config()

    def test_load_config_raises_when_destination_root_missing(self, monkeypatch):
        monkeypatch.delenv("PHOTO_IMPORT_MOUNT_POINT", raising=False)
        monkeypatch.delenv("PHOTO_IMPORT_DESTINATION_ROOT", raising=False)
        monkeypatch.setenv("PHOTO_IMPORT_MOUNT_POINT", "/src")

        with pytest.raises(ConfigurationError, match="PHOTO_IMPORT_DESTINATION_ROOT"):
            load_config()

    def test_load_config_returns_config_when_both_set(self, monkeypatch):
        monkeypatch.setenv("PHOTO_IMPORT_MOUNT_POINT", "/src")
        monkeypatch.setenv("PHOTO_IMPORT_DESTINATION_ROOT", "/dest")

        config = load_config()

        assert config.mount_point == Path("/src")
        assert config.destination_root == Path("/dest")
