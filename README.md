# `dropfix`

> [!TIP]
> Dropbox Directory Ignore Tools

`dropfix` helps you configure Dropbox to ignore specific development directories (`.venv`, `.conda`, `node_modules`) that don't need to be synced across machines.

## Quick Start

### Platform-Specific Scripts

- **Windows**: Run `dropfix-win.ps1` in PowerShell
- **Linux**: Run `dropfix-nix.sh` in Bash
- **macOS**: Run `dropfix-mac.sh` in Terminal

### Cross-Platform Python Scripts

#### Setting Ignored Directories

- **All Platforms**: Run `dropfix.py` with Python 3

  ```bash
  # Basic usage (auto-detects Dropbox path)
  python3 dropfix.py

  # Dry run mode (shows what would happen without making changes)
  python3 dropfix.py --dry-run

  # Specify custom Dropbox path
  python3 dropfix.py --path /path/to/your/Dropbox

  # Ignore specific directories
  python3 dropfix.py --dirs .venv .cache node_modules
  ```

#### Checking Ignored Status

- **All Platforms**: Run `dropfix-check.py` with Python 3

  ```bash
  # Check which directories are ignored (auto-detects Dropbox path)
  python3 dropfix-check.py

  # Show only ignored directories
  python3 dropfix-check.py --show ignored

  # Show only not-ignored directories
  python3 dropfix-check.py --show not-ignored

  # Specify custom directories to check
  python3 dropfix-check.py --dirs .venv node_modules vendor
  ```

## Why These Tools?

- **Save Space**: Avoid syncing large development directories
- **Improve Performance**: Reduce Dropbox sync operations
- **Cross-Platform Compatible**: Works across different operating systems

## Cross-Platform Safety

These scripts set the same `com.dropbox.ignored` attribute (with value `1`) that Dropbox recognizes across all platforms:

- Windows uses NTFS alternate data streams
- macOS uses extended attributes
- Linux uses file attributes

You can safely use Windows machines, macOS, and Linux with the same Dropbox account without conflicts.

## Advanced Configuration

For additional ways to configure Dropbox ignore patterns, including:

- Using `.dropboxignore` (Business accounts)
- Setting sync exclusion lists
- Manual command-line operations

See the [Advanced Dropbox Ignore Tools](./db-ignore.md).

## After Running Scripts

Remember to restart Dropbox for the changes to take effect.

## Note About Paths

These scripts include hardcoded paths (`C:\Users\shane\Dropbox` for Windows and `$HOME/Dropbox` for macOS/Linux) for convenience. Before running, you may need to:

1. Open the script in a text editor
2. Change the `$dropboxPath` variable to match your Dropbox location
3. Save the file

The scripts were originally created for personal use, so these paths were hardcoded to bypass additional configuration questions.
