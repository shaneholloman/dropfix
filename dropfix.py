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
    parser = argparse.ArgumentParser(description="Dropfix: Ignore development directories in Dropbox")
    parser.add_argument("--path", help="Path to Dropbox directory (default: auto-detect)")
    parser.add_argument("--dirs", nargs="+", default=[".venv", ".conda", "node_modules"],
                        help="Directory names to ignore (default: .venv .conda node_modules)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without making changes")
    args = parser.parse_args()

    # Auto-detect or use provided Dropbox path
    dropbox_path = args.path or find_dropbox_path()
    if not dropbox_path:
        print(f"{RED}Error: Could not find Dropbox directory.{RESET}")
        print(f"{YELLOW}Please specify your Dropbox path with --path{RESET}")
        return 1

    # Show configuration and confirm
    if args.dry_run:
        print(f"\n{YELLOW}=== DRY RUN MODE - No changes will be made ==={RESET}\n")

    print(f"Will {CYAN}{'simulate ignoring' if args.dry_run else 'ignore'}{RESET} these directories in {CYAN}{dropbox_path}{RESET}:")
    for dir_name in args.dirs:
        print(f"- {YELLOW}{dir_name}{RESET}")

    if not args.dry_run:
        confirm = input(f"\nProceed? (y/n): ")
        if confirm.lower() != 'y':
            return 0

    # Find and ignore directories
    process_directories(dropbox_path, args.dirs, dry_run=args.dry_run)
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

def process_directories(dropbox_path, dir_names, dry_run=False):
    """Find and process directories to ignore"""
    system = platform.system()
    ignored_count = 0
    error_count = 0

    # Find all matching directories
    for dir_name in dir_names:
        print(f"\n{CYAN}Searching for '{dir_name}' directories...{RESET}")
        matches = []

        try:
            # Use os.walk to avoid recursive glob limitations in some Python versions
            for root, dirs, _ in os.walk(dropbox_path):
                for d in dirs:
                    if d == dir_name:
                        matches.append(Path(root) / d)
        except Exception as e:
            print(f"{RED}Error searching for directories: {e}{RESET}")

        if not matches:
            print(f"{GRAY}No '{dir_name}' directories found.{RESET}")
            continue

        print(f"{GREEN}Found {len(matches)} '{dir_name}' directories to process.{RESET}\n")

        # Process each directory
        for i, dir_path in enumerate(matches, 1):
            progress_bar(i, len(matches))

            try:
                if dry_run:
                    # Just show what would happen
                    if i == len(matches):  # Only show for the last item to avoid cluttering
                        print(f"\n\n{YELLOW}Would set com.dropbox.ignored=1 on: {dir_path}{RESET}")
                    ignored_count += 1
                elif ignore_directory(dir_path, system):
                    ignored_count += 1
                else:
                    error_count += 1
            except Exception as e:
                print(f"\n{RED}Error {'simulating' if dry_run else 'ignoring'} {dir_path}: {e}{RESET}")
                error_count += 1

        print(f"\n{GREEN}Completed {'simulating' if dry_run else 'processing'} '{dir_name}' directories.{RESET}")

    # Summary
    if dry_run:
        print(f"\n{YELLOW}=== DRY RUN SUMMARY (No changes were made) ==={RESET}\n")
    print(f"Total directories {'that would be processed' if dry_run else 'processed'}: {CYAN}{ignored_count}{RESET}")
    if error_count > 0:
        print(f"{RED}Errors {'that would be' if dry_run else ''} encountered: {error_count}{RESET}")

    if not dry_run:
        print(f"\n{YELLOW}Note: You may need to restart Dropbox for changes to take effect.{RESET}")

def ignore_directory(path, system):
    """Set the appropriate attribute based on OS"""
    path_str = str(path)

    try:
        if system == "Windows":
            # Windows: NTFS alternate data streams
            subprocess.run(
                ["powershell", "-Command", f"Set-Content -Path '{path_str}' -Stream com.dropbox.ignored -Value 1"],
                check=True, capture_output=True
            )
        elif system == "Darwin":  # macOS
            # macOS: extended attributes
            subprocess.run(
                ["xattr", "-w", "com.dropbox.ignored", "1", path_str],
                check=True, capture_output=True
            )
        else:  # Linux and others
            # Linux: attributes
            subprocess.run(
                ["attr", "-s", "com.dropbox.ignored", "-V", "1", path_str],
                check=True, capture_output=True
            )
        return True
    except subprocess.CalledProcessError:
        return False

def progress_bar(current, total, width=50):
    """Display a simple progress bar"""
    percent = current / total
    filled = int(width * percent)
    bar = f"{GREEN}{'#' * filled}{GRAY}{'-' * (width - filled)}{RESET}"
    sys.stdout.write(f"\r[{bar}] {CYAN}{percent:.0%}{RESET} ({current}/{total})")
    sys.stdout.flush()

if __name__ == "__main__":
    sys.exit(main())
