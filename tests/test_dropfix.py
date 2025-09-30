"""Tests for dropfix core functionality"""
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dropfix.dropfix import find_dropbox_path, ignore_directory, process_directories


class TestFindDropboxPath:
    """Tests for Dropbox path auto-detection"""

    def test_finds_dropbox_in_home(self, tmp_path, monkeypatch):
        """Should find Dropbox in home directory"""
        dropbox_dir = tmp_path / "Dropbox"
        dropbox_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = find_dropbox_path()
        assert result == dropbox_dir

    def test_finds_dropbox_in_documents(self, tmp_path, monkeypatch):
        """Should find Dropbox in Documents directory"""
        docs_dir = tmp_path / "Documents"
        docs_dir.mkdir()
        dropbox_dir = docs_dir / "Dropbox"
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
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "xattr"
        assert call_args[1] == "-w"
        assert call_args[2] == "com.dropbox.ignored"

    @patch("dropfix.dropfix.subprocess.run")
    def test_macos_failure(self, mock_run):
        """Should return False when xattr command fails"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "xattr")
        path = Path("/test/path")

        result = ignore_directory(path, "Darwin")

        assert result is False

    @patch("dropfix.dropfix.subprocess.run")
    def test_linux_success(self, mock_run):
        """Should successfully ignore directory on Linux"""
        mock_run.return_value = Mock(returncode=0)
        path = Path("/test/path")

        result = ignore_directory(path, "Linux")

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "attr"
        assert call_args[1] == "-s"
        assert call_args[2] == "com.dropbox.ignored"

    @patch("dropfix.dropfix.subprocess.run")
    def test_windows_success(self, mock_run):
        """Should successfully ignore directory on Windows"""
        mock_run.return_value = Mock(returncode=0)
        path = Path("C:\\test\\path")

        result = ignore_directory(path, "Windows")

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "powershell"
        assert "Set-Content" in call_args[2]


class TestProcessDirectories:
    """Tests for process_directories function"""

    @patch("dropfix.dropfix.ignore_directory")
    @patch("dropfix.dropfix.os.walk")
    def test_dry_run_mode(self, mock_walk, mock_ignore, tmp_path):
        """Should not call ignore_directory in dry-run mode"""
        venv_dir = tmp_path / ".venv"
        mock_walk.return_value = [(str(tmp_path), [".venv"], [])]

        process_directories(tmp_path, [".venv"], dry_run=True)

        mock_ignore.assert_not_called()

    @patch("dropfix.dropfix.ignore_directory")
    @patch("dropfix.dropfix.os.walk")
    def test_processes_multiple_directories(self, mock_walk, mock_ignore, tmp_path):
        """Should process all matching directories"""
        mock_walk.return_value = [
            (str(tmp_path), [".venv", ".conda"], []),
            (str(tmp_path / "project"), [".venv"], []),
        ]
        mock_ignore.return_value = True

        process_directories(tmp_path, [".venv", ".conda"], dry_run=False)

        # Should have called ignore_directory for: .venv, .conda, and nested .venv
        assert mock_ignore.call_count == 3

    @patch("dropfix.dropfix.ignore_directory")
    @patch("dropfix.dropfix.os.walk")
    def test_handles_permission_errors(self, mock_walk, mock_ignore, tmp_path):
        """Should continue processing after permission errors"""
        mock_walk.side_effect = PermissionError("Access denied")

        # Should not raise exception
        process_directories(tmp_path, [".venv"], dry_run=False)

        mock_ignore.assert_not_called()