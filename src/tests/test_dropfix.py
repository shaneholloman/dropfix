"""Tests for dropfix core functionality"""
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch


from dropfix.dropfix import find_dropbox_path, ignore_directory


class TestFindDropboxPath:
    """Tests for Dropbox path auto-detection"""

    def test_finds_dropbox_in_home(self, tmp_path, monkeypatch):
        """Should find Dropbox in home directory"""
        dropbox_dir = tmp_path / "Dropbox"
        dropbox_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = find_dropbox_path()
        assert result == dropbox_dir

    def test_returns_none_when_not_found(self, tmp_path, monkeypatch):
        """Should return None when Dropbox directory doesn't exist"""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = find_dropbox_path()
        assert result is None


class TestIgnoreDirectory:
    """Tests for ignore_directory function"""

    @patch("dropfix.dropfix.subprocess.run")
    def test_macos_success(self, mock_run):
        """Should successfully ignore directory on macOS"""
        mock_run.return_value = Mock(returncode=0)
        path = Path("/test/path")

        result = ignore_directory(path, "Darwin")

        assert result is True
        mock_run.assert_called_once()

    @patch("dropfix.dropfix.subprocess.run")
    def test_macos_failure(self, mock_run):
        """Should return False when xattr command fails"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "xattr")
        path = Path("/test/path")

        result = ignore_directory(path, "Darwin")

        assert result is False
