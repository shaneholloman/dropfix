#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
from pathlib import Path
import argparse

# ANSI color codes
CYAN = '\033[0;36m'
YELLOW = '\033[0;33m'
GREEN = '\033[0;32m'
RED = '\033[0;31m'
GRAY = '\033[0;37m'
RESET = '\033[0m'  # Reset color

def main():
    parser = argparse.ArgumentParser(description="Dropfix-Check: Verify directories ignored by Dropbox")
    parser.add_argument("--path", help="Path to Dropbox directory (default: auto-detect)")
    parser.add_argument("--dirs", nargs="+", default=[".venv", ".conda", "node_modules"],
                        help="Directory names to check (default: .venv .conda node_modules)")
    parser.add_argument("--show", choices=["all", "ignored", "not-ignored"], default="all",
                        help="Filter which directories to show (default: all)")
    args = parser.parse_args()

    # Auto-detect or use provided Dropbox path
    dropbox_path = args.path or find_dropbox_path()
    if not dropbox_path:
        print(f"{RED}Error: Could not find Dropbox directory.{RESET}")
        print(f"{YELLOW}Please specify your Dropbox path with --path{RESET}")
        return 1

    # Show configuration
    print(f"\n{CYAN}Checking directories in {dropbox_path}{RESET}")
    print(f"Looking for: {', '.join(f'{YELLOW}{d}{RESET}' for d in args.dirs)}")
    print(f"Showing: {YELLOW}{args.show}{RESET}\n")

    # Check directories
    check_directories(dropbox_path, args.dirs, args.show)
    return 0

def find_dropbox_path():
    """Auto-detect Dropbox path based on common locations"""
    home = Path.home()
    common_paths = [
        home / "Dropbox",
        home / "Documents" / "Dropbox"
    ]

    # Windows-specific paths
    if platform.system() == "Windows":
        common_paths.extend([
            Path(os.environ.get('USERPROFILE', '')) / "Dropbox",
            Path(os.environ.get('HOMEDRIVE', '') + os.environ.get('HOMEPATH', '')) / "Dropbox"
        ])

    for path in common_paths:
        if path.exists() and path.is_dir():
            return path

    return None

def check_directories(dropbox_path, dir_names, show_filter="all"):
    """Find directories and check if they're ignored by Dropbox"""
    system = platform.system()
    ignored_count = 0
    not_ignored_count = 0
    error_count = 0

    # Find all matching directories
    all_matches = []
    for dir_name in dir_names:
        print(f"{CYAN}Searching for '{dir_name}' directories...{RESET}")
        matches = []

        try:
            # Use os.walk to find all matching directories
            for root, dirs, _ in os.walk(dropbox_path):
                for d in dirs:
                    if d == dir_name:
                        matches.append(Path(root) / d)
        except Exception as e:
            print(f"{RED}Error searching for directories: {e}{RESET}")

        if not matches:
            print(f"{GRAY}No '{dir_name}' directories found.{RESET}\n")
            continue

        print(f"{GREEN}Found {len(matches)} '{dir_name}' directories.{RESET}\n")
        all_matches.extend(matches)

    if not all_matches:
        print(f"{YELLOW}No matching directories found.{RESET}")
        return

    print(f"{CYAN}Checking Dropbox ignore status for {len(all_matches)} directories...{RESET}\n")

    # Check each directory
    ignored_dirs = []
    not_ignored_dirs = []
    error_dirs = []

    for i, dir_path in enumerate(all_matches, 1):
        progress_bar(i, len(all_matches))

        try:
            is_ignored = check_if_ignored(dir_path, system)
            if is_ignored is True:
                ignored_dirs.append(dir_path)
                ignored_count += 1
            elif is_ignored is False:
                not_ignored_dirs.append(dir_path)
                not_ignored_count += 1
            else:  # None = error
                error_dirs.append(dir_path)
                error_count += 1
        except Exception as e:
            print(f"\n{RED}Error checking {dir_path}: {e}{RESET}")
            error_dirs.append(dir_path)
            error_count += 1

    # Print results
    print("\n")  # Extra newline after progress bar

    # Ignored directories
    if show_filter in ["all", "ignored"] and ignored_dirs:
        print(f"\n{GREEN}=== Directories ignored by Dropbox ({len(ignored_dirs)}) ==={RESET}\n")
        for d in ignored_dirs:
            print(f"{GREEN}✓ {d}{RESET}")

    # Not ignored directories
    if show_filter in ["all", "not-ignored"] and not_ignored_dirs:
        print(f"\n{YELLOW}=== Directories NOT ignored by Dropbox ({len(not_ignored_dirs)}) ==={RESET}\n")
        for d in not_ignored_dirs:
            print(f"{YELLOW}✗ {d}{RESET}")

    # Errors
    if error_dirs:
        print(f"\n{RED}=== Directories with check errors ({len(error_dirs)}) ==={RESET}\n")
        for d in error_dirs:
            print(f"{RED}! {d}{RESET}")

    # Summary
    print(f"\n{CYAN}=== Summary ==={RESET}\n")
    print(f"Total directories checked: {ignored_count + not_ignored_count + error_count}")
    print(f"{GREEN}Ignored by Dropbox: {ignored_count}{RESET}")
    print(f"{YELLOW}Not ignored: {not_ignored_count}{RESET}")
    if error_count > 0:
        print(f"{RED}Check errors: {error_count}{RESET}")

def check_if_ignored(path, system):
    """Check if a directory is ignored by Dropbox

    Returns:
        True: Directory is ignored
        False: Directory is not ignored
        None: Could not determine (error)
    """
    path_str = str(path)

    try:
        if system == "Windows":
            # Windows: Check NTFS alternate data streams
            result = subprocess.run(
                ["powershell", "-Command", f"Get-Content -Path '{path_str}' -Stream com.dropbox.ignored -ErrorAction SilentlyContinue"],
                capture_output=True, text=True, check=False
            )
            # If command succeeds and value is "1", directory is ignored
            return result.returncode == 0 and result.stdout.strip() == "1"

        elif system == "Darwin":  # macOS
            # macOS: Check extended attributes
            result = subprocess.run(
                ["xattr", "-p", "com.dropbox.ignored", path_str],
                capture_output=True, text=True, check=False
            )
            # If command succeeds and value is "1", directory is ignored
            return result.returncode == 0 and result.stdout.strip() == "1"

        else:  # Linux and others
            # Linux: Check attributes
            result = subprocess.run(
                ["attr", "-q", "-g", "com.dropbox.ignored", path_str],
                capture_output=True, text=True, check=False
            )
            # If command succeeds and value contains "1", directory is ignored
            return result.returncode == 0 and "1" in result.stdout.strip()

    except Exception:
        return None  # Error occurred

    return False  # Default: not ignored

def progress_bar(current, total, width=50):
    """Display a simple progress bar"""
    percent = current / total
    filled = int(width * percent)
    bar = f"{GREEN}{'#' * filled}{GRAY}{'-' * (width - filled)}{RESET}"
    sys.stdout.write(f"\r[{bar}] {CYAN}{percent:.0%}{RESET} ({current}/{total})")
    sys.stdout.flush()

if __name__ == "__main__":
    sys.exit(main())
