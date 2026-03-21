from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestSafeUnmount:
    def test_should_return_true_when_not_mounted(self):
        from photo_import.cleanup import safe_unmount

        # Arrange
        logger = MagicMock()
        with patch("photo_import.cleanup.is_mountpoint", return_value=False):
            # Act
            result = safe_unmount(Path("/mnt/test"), logger)

        # Assert
        assert result is True
        logger.info.assert_not_called()

    def test_should_unmount_and_return_true_on_success(self):
        from photo_import.cleanup import safe_unmount

        # Arrange
        logger = MagicMock()
        with patch("photo_import.cleanup.is_mountpoint", return_value=True):
            with patch("photo_import.cleanup.unmount_device"):
                # Act
                result = safe_unmount(Path("/mnt/test"), logger)

        # Assert
        assert result is True
        logger.info.assert_called_once()

    def test_should_return_false_and_log_exception_on_failure(self):
        from photo_import.cleanup import safe_unmount

        # Arrange
        logger = MagicMock()
        with patch("photo_import.cleanup.is_mountpoint", return_value=True):
            with patch(
                "photo_import.cleanup.unmount_device", side_effect=Exception("busy")
            ):
                # Act
                result = safe_unmount(Path("/mnt/test"), logger)

        # Assert
        assert result is False
        logger.exception.assert_called_once()
