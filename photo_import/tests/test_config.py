from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

import pytest
from photo_import import config as config_module

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
        config = config_module.Config()

        assert config.log_file is None
        assert config.log_level == logging.INFO
        assert config.lock_file == Path()
        assert config.mount_point is None
        assert config.destination_root is None


class TestLoadConfig:
    def test_load_config_raises_when_mount_point_missing(self, monkeypatch):
        env = {
            "PHOTO_IMPORT_LOCK_FILE": "/tmp/photo-import.lock",
            "PHOTO_IMPORT_DESTINATION_ROOT": "/dest",
        }

        with pytest.raises(
            config_module.ConfigurationError, match="PHOTO_IMPORT_MOUNT_POINT"
        ):
            config_module.load_config(env)

    def test_load_config_raises_when_destination_root_missing(self, monkeypatch):
        env = {
            "PHOTO_IMPORT_LOCK_FILE": "/tmp/photo-import.lock",
            "PHOTO_IMPORT_MOUNT_POINT": "/src",
        }

        with pytest.raises(
            config_module.ConfigurationError, match="PHOTO_IMPORT_DESTINATION_ROOT"
        ):
            config_module.load_config(env)

    def test_load_config_returns_config_when_both_set(self):
        env = {
            "PHOTO_IMPORT_MOUNT_POINT": "/src",
            "PHOTO_IMPORT_DESTINATION_ROOT": "/dest",
            "PHOTO_IMPORT_LOG_FILE": "/var/log/photo-import.log",
            "PHOTO_IMPORT_LOG_LEVEL": "DEBUG",
            "PHOTO_IMPORT_LOCK_FILE": "/custom/lock",
        }

        config = config_module.load_config(env)

        assert config.log_file == Path("/var/log/photo-import.log")
        assert config.log_level == logging.DEBUG
        assert config.lock_file == Path("/custom/lock")
        assert config.mount_point == Path("/src")
        assert config.destination_root == Path("/dest")

    def test_load_config_treats_empty_log_path_as_unset(self):
        env = {
            "PHOTO_IMPORT_MOUNT_POINT": "/src",
            "PHOTO_IMPORT_DESTINATION_ROOT": "/dest",
            "PHOTO_IMPORT_LOG_FILE": "",
            "PHOTO_IMPORT_LOCK_FILE": "/tmp/photo-import.lock",
        }

        config = config_module.load_config(env)

        assert config.log_file is None
        assert config.log_level == logging.INFO

    def test_load_config_raises_when_lock_file_missing(self):
        env = {
            "PHOTO_IMPORT_MOUNT_POINT": "/src",
            "PHOTO_IMPORT_DESTINATION_ROOT": "/dest",
        }

        with pytest.raises(
            config_module.ConfigurationError, match="PHOTO_IMPORT_LOCK_FILE"
        ):
            config_module.load_config(env)

    def test_load_config_defaults_to_os_environ(self, monkeypatch):
        monkeypatch.setenv("PHOTO_IMPORT_MOUNT_POINT", "/src")
        monkeypatch.setenv("PHOTO_IMPORT_DESTINATION_ROOT", "/dest")
        monkeypatch.setenv("PHOTO_IMPORT_LOCK_FILE", "/tmp/photo-import.lock")

        config = config_module.load_config()

        assert config.mount_point == Path("/src")
        assert config.destination_root == Path("/dest")
        assert config.lock_file == Path("/tmp/photo-import.lock")

    def test_load_config_raises_when_log_level_invalid(self):
        env = {
            "PHOTO_IMPORT_MOUNT_POINT": "/src",
            "PHOTO_IMPORT_DESTINATION_ROOT": "/dest",
            "PHOTO_IMPORT_LOCK_FILE": "/tmp/photo-import.lock",
            "PHOTO_IMPORT_LOG_LEVEL": "verbose",
        }

        with pytest.raises(
            config_module.ConfigurationError, match="PHOTO_IMPORT_LOG_LEVEL"
        ):
            config_module.load_config(env)
