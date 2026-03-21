from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class MockCompletedProcess:
    def __init__(self, returncode: int):
        self.returncode = returncode


class TestIsMountpoint:
    def test_should_return_true_when_mountpoint_command_succeeds(self):
        from photo_import.mount import is_mountpoint

        # Arrange
        path = Path("/mnt/test")
        with patch("photo_import.mount.subprocess.run") as mock_run:
            mock_run.return_value = MockCompletedProcess(returncode=0)

            # Act
            result = is_mountpoint(path)

        # Assert
        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "mountpoint"
        assert "-q" in args
        assert args[-1] == "/mnt/test"

    def test_should_return_false_when_mountpoint_command_fails(self):
        from photo_import.mount import is_mountpoint

        # Arrange
        with patch("photo_import.mount.subprocess.run") as mock_run:
            mock_run.return_value = MockCompletedProcess(returncode=1)

            # Act
            result = is_mountpoint(Path("/mnt/test"))

        # Assert
        assert result is False

    def test_should_return_false_when_mountpoint_returns_nonzero(self):
        from photo_import.mount import is_mountpoint

        # Arrange
        with patch("photo_import.mount.subprocess.run") as mock_run:
            mock_run.return_value = MockCompletedProcess(returncode=32)

            # Act
            result = is_mountpoint(Path("/mnt/test"))

        # Assert
        assert result is False


class TestMountDevice:
    def test_should_call_mount_with_read_only_option(self, tmp_path):
        from photo_import.mount import mount_device

        # Arrange
        with patch("photo_import.mount.subprocess.run") as mock_run:
            mock_run.return_value = MockCompletedProcess(returncode=0)

            # Act
            mount_device("/dev/sda1", tmp_path, read_only=True)

        # Assert
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "mount"
        assert "ro" in args
        assert "-o" in args

    def test_should_call_mount_with_read_write_option(self, tmp_path):
        from photo_import.mount import mount_device

        # Arrange
        with patch("photo_import.mount.subprocess.run") as mock_run:
            mock_run.return_value = MockCompletedProcess(returncode=0)

            # Act
            mount_device("/dev/sda1", tmp_path, read_only=False)

        # Assert
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "mount"
        assert "rw" in args

    def test_should_create_mount_point_directory(self, tmp_path):
        from photo_import.mount import mount_device

        # Arrange
        mount_point = tmp_path / "new" / "dir"
        with patch("photo_import.mount.subprocess.run"):
            # Act
            mount_device("/dev/sda1", mount_point, read_only=True)

        # Assert
        assert mount_point.exists()


class TestUnmountDevice:
    def test_should_call_umount_with_correct_args(self):
        from photo_import.mount import unmount_device

        # Arrange
        with patch("photo_import.mount.subprocess.run") as mock_run:
            mock_run.return_value = MockCompletedProcess(returncode=0)

            # Act
            unmount_device(Path("/mnt/test"))

        # Assert
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "umount"
        assert "/mnt/test" in args

    def test_should_raise_on_unmount_failure(self):
        from photo_import.mount import unmount_device

        # Arrange
        mock_run = MagicMock()
        mock_run.side_effect = Exception("umount failed")

        # Act & Assert
        with patch("photo_import.mount.subprocess.run", mock_run):
            with pytest.raises(Exception, match="umount failed"):
                unmount_device(Path("/mnt/test"))
