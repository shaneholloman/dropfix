"""Tests for dropfix-check functionality"""
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dropfix._checker import check_if_ignored, organize_directories


class TestCheckIfIgnored:
    """Tests for check_if_ignored function"""

    @patch("dropfix._checker.subprocess.run")
    def test_macos_ignored(self, mock_run):
        """Should return True when directory is ignored on macOS"""
        mock_run.return_value = Mock(returncode=0, stdout="1\n")
        path = Path("/test/path")

        result = check_if_ignored(path, "Darwin")

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "xattr"
        assert call_args[1] == "-p"
        assert call_args[2] == "com.dropbox.ignored"

    @patch("dropfix._checker.subprocess.run")
    def test_macos_not_ignored(self, mock_run):
        """Should return False when directory is not ignored on macOS"""
        mock_run.return_value = Mock(returncode=1, stdout="")
        path = Path("/test/path")

        result = check_if_ignored(path, "Darwin")

        assert result is False

    @patch("dropfix._checker.subprocess.run")
    def test_linux_ignored(self, mock_run):
        """Should return True when directory is ignored on Linux"""
        mock_run.return_value = Mock(returncode=0, stdout="1")
        path = Path("/test/path")

        result = check_if_ignored(path, "Linux")

        assert result is True

    @patch("dropfix._checker.subprocess.run")
    def test_windows_ignored(self, mock_run):
        """Should return True when directory is ignored on Windows"""
        mock_run.return_value = Mock(returncode=0, stdout="1")
        path = Path("C:\\test\\path")

        result = check_if_ignored(path, "Windows")

        assert result is True

    @patch("dropfix._checker.subprocess.run")
    def test_error_returns_none(self, mock_run):
        """Should return None when check fails"""
        mock_run.side_effect = PermissionError("Access denied")
        path = Path("/test/path")

        result = check_if_ignored(path, "Darwin")

        assert result is None


class TestOrganizeDirectories:
    """Tests for organize_directories function"""

    def test_single_directory(self, tmp_path):
        """Should handle single directory"""
        paths = [tmp_path / ".venv"]

        top_level, nested_counts = organize_directories(paths, tmp_path)

        assert len(top_level) == 1
        assert top_level[0] == paths[0]
        assert nested_counts[paths[0]] == 0

    def test_nested_directories(self, tmp_path):
        """Should identify nested directories"""
        parent = tmp_path / "project" / ".venv"
        child = tmp_path / "project" / ".venv" / "lib" / ".venv"
        paths = [parent, child]

        top_level, nested_counts = organize_directories(paths, tmp_path)

        assert len(top_level) == 1
        assert top_level[0] == parent
        assert nested_counts[parent] == 1

    def test_multiple_top_level(self, tmp_path):
        """Should identify multiple top-level directories"""
        path1 = tmp_path / "project1" / ".venv"
        path2 = tmp_path / "project2" / ".venv"
        paths = [path1, path2]

        top_level, nested_counts = organize_directories(paths, tmp_path)

        assert len(top_level) == 2
        assert path1 in top_level
        assert path2 in top_level
        assert nested_counts[path1] == 0
        assert nested_counts[path2] == 0

    def test_deeply_nested(self, tmp_path):
        """Should handle deeply nested structures"""
        parent = tmp_path / ".venv"
        child1 = tmp_path / ".venv" / "a" / ".venv"
        child2 = tmp_path / ".venv" / "a" / "b" / ".venv"
        paths = [parent, child1, child2]

        top_level, nested_counts = organize_directories(paths, tmp_path)

        assert len(top_level) == 1
        assert top_level[0] == parent
        assert nested_counts[parent] == 2