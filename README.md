# ``dropfix``

> [!TIP]
> Dropbox Directory Ignore Tools

`dropfix` helps you configure Dropbox to ignore specific development directories (`.venv`, `.conda`, `node_modules`) that don't need to be synced across machines.

## Quick Start

- **Windows**: Run `ignore-dropbox-dirs.ps1` in PowerShell
- **Linux**: Run `ignore-dropbox-dirs.sh` in Bash
- **macOS**: Run `ignore-dropbox-dirs-mac.sh` in Terminal

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
