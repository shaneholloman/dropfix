#!/usr/bin/env python3
import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

# ANSI color codes
CYAN = "\033[0;36m"
YELLOW = "\033[0;33m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
GRAY = "\033[0;37m"
RESET = "\033[0m"  # Reset color


def main():
    parser = argparse.ArgumentParser(description="Dropfix-Check: Verify directories ignored by Dropbox")
    parser.add_argument("--path", help="Path to Dropbox directory (default: auto-detect)")
    parser.add_argument(
        "--dirs",
        nargs="+",
        default=[".venv", ".conda", "node_modules"],
        help="Directory names to check (default: .venv .conda node_modules)",
    )
    parser.add_argument(
        "--show",
        choices=["all", "ignored", "not-ignored"],
        default="all",
        help="Filter which directories to show (default: all)",
    )
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
    common_paths = [home / "Dropbox", home / "Documents" / "Dropbox"]

    # Windows-specific paths
    if platform.system() == "Windows":
        common_paths.extend([
            Path(os.environ.get("USERPROFILE", "")) / "Dropbox",
            Path(os.environ.get("HOMEDRIVE", "") + os.environ.get("HOMEPATH", "")) / "Dropbox",
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

    # Track directories by name for grouping
    dir_groups = {name: [] for name in dir_names}

    # Find all matching directories
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
        dir_groups[dir_name].extend(matches)

    # Combine all directories for processing
    all_matches = []
    for matches in dir_groups.values():
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

    # Group ignored directories by name and parent-child relationships
    ignored_by_name = {}
    for d in ignored_dirs:
        dir_name = d.name
        if dir_name not in ignored_by_name:
            ignored_by_name[dir_name] = []
        ignored_by_name[dir_name].append(d)

    # Print results
    print("\n")  # Extra newline after progress bar

    # Ignored directories - grouped and filtered
    if show_filter in ["all", "ignored"] and ignored_dirs:
        print(f"\n{GREEN}=== Directories ignored by Dropbox ({len(ignored_dirs)}) ==={RESET}\n")

        for dir_name, paths in ignored_by_name.items():
            # Get organized hierarchy of directories
            top_level_dirs, nested_counts = organize_directories(paths, dropbox_path)

            # Show only top-level directories with nested counts
            for top_dir in top_level_dirs:
                nested_count = nested_counts.get(top_dir, 0)
                if nested_count > 0:
                    print(f"{GREEN}✓ {top_dir} {CYAN}(+{nested_count} nested ignored directories){RESET}")
                else:
                    print(f"{GREEN}✓ {top_dir}{RESET}")

    # Not ignored directories
    if show_filter in ["all", "not-ignored"] and not_ignored_dirs:
        print(f"\n{YELLOW}=== Directories NOT ignored by Dropbox ({len(not_ignored_dirs)}) ==={RESET}\n")

        # Group not-ignored directories by name
        not_ignored_by_name = {}
        for d in not_ignored_dirs:
            dir_name = d.name
            if dir_name not in not_ignored_by_name:
                not_ignored_by_name[dir_name] = []
            not_ignored_by_name[dir_name].append(d)

        for dir_name, paths in not_ignored_by_name.items():
            # Get organized hierarchy
            top_level_dirs, nested_counts = organize_directories(paths, dropbox_path)

            # Show only top-level directories with nested counts
            for top_dir in top_level_dirs:
                nested_count = nested_counts.get(top_dir, 0)
                if nested_count > 0:
                    print(f"{YELLOW}✗ {top_dir} {CYAN}(+{nested_count} nested non-ignored directories){RESET}")
                else:
                    print(f"{YELLOW}✗ {top_dir}{RESET}")

    # Errors
    if error_dirs:
        print(f"\n{RED}=== Directories with check errors ({len(error_dirs)}) ==={RESET}\n")

        # Group error directories by name
        error_by_name = {}
        for d in error_dirs:
            dir_name = d.name
            if dir_name not in error_by_name:
                error_by_name[dir_name] = []
            error_by_name[dir_name].append(d)

        for dir_name, paths in error_by_name.items():
            # Get organized hierarchy
            top_level_dirs, nested_counts = organize_directories(paths, dropbox_path)

            # Show only top-level directories with nested counts
            for top_dir in top_level_dirs:
                nested_count = nested_counts.get(top_dir, 0)
                if nested_count > 0:
                    print(f"{RED}! {top_dir} {CYAN}(+{nested_count} nested error directories){RESET}")
                else:
                    print(f"{RED}! {top_dir}{RESET}")

    # Summary
    print(f"\n{CYAN}=== Summary ==={RESET}\n")
    print(f"Total directories checked: {ignored_count + not_ignored_count + error_count}")
    print(f"{GREEN}Ignored by Dropbox: {ignored_count}{RESET}")
    print(f"{YELLOW}Not ignored: {not_ignored_count}{RESET}")
    if error_count > 0:
        print(f"{RED}Check errors: {error_count}{RESET}")


def organize_directories(paths, base_path):
    """Organize directories into a hierarchy of parent-child relationships

    Args:
        paths: List of Path objects to organize
        base_path: Base path to consider as root for relative paths

    Returns:
        tuple: (top_level_dirs, nested_counts)
            - top_level_dirs: List of top-level directories
            - nested_counts: Dict mapping top-level dirs to count of nested dirs
    """
    # Sort paths by depth (shortest paths first)
    sorted_paths = sorted(paths, key=lambda p: len(str(p).split(os.sep)))

    # Find top-level directories and count nested directories
    top_level_dirs = []
    nested_counts = {}
    path_parents = {}

    for path in sorted_paths:
        # Check if this path is under any already processed path
        is_nested = False
        parent_path = None

        # Convert to string for easier path operations
        path_str = str(path)

        for existing_path in top_level_dirs:
            existing_str = str(existing_path)
            # If this path starts with an existing path plus a separator, it's nested
            if path_str.startswith(existing_str + os.sep):
                is_nested = True
                parent_path = existing_path
                # Increment the nested count for the parent path
                nested_counts[existing_path] += 1
                break

        if not is_nested:
            # This is a top-level directory
            top_level_dirs.append(path)
            nested_counts[path] = 0

        # Track the parent for this path
        if parent_path:
            path_parents[path] = parent_path

    return top_level_dirs, nested_counts


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
                [
                    "powershell",
                    "-Command",
                    f"Get-Content -Path '{path_str}' -Stream com.dropbox.ignored -ErrorAction SilentlyContinue",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            # If command succeeds and value is "1", directory is ignored
            return result.returncode == 0 and result.stdout.strip() == "1"

        elif system == "Darwin":  # macOS
            # macOS: Check extended attributes
            result = subprocess.run(
                ["xattr", "-p", "com.dropbox.ignored", path_str], capture_output=True, text=True, check=False
            )
            # If command succeeds and value is "1", directory is ignored
            return result.returncode == 0 and result.stdout.strip() == "1"

        else:  # Linux and others
            # Linux: Check attributes
            result = subprocess.run(
                ["attr", "-q", "-g", "com.dropbox.ignored", path_str], capture_output=True, text=True, check=False
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
