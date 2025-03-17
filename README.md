# Dropbox Directory Ignore Scripts

These scripts help you configure Dropbox to ignore specific development directories (`.venv`, `.conda`, `node_modules`) that don't need to be synced across machines.

## Usage

- On Windows: Run `ignore-dropbox-dirs.ps1` using PowerShell
- On Linux/macOS: Run `ignore-dropbox-dirs.sh` using Bash

## Cross-Platform Safety

These scripts can be safely used on the same Dropbox folder across different operating systems. Here's why:

1. Both scripts set the exact same Dropbox-specific attribute (`com.dropbox.ignored`) with the same value (`1`)
2. The only difference is how each operating system stores this attribute:
   - Windows uses NTFS alternate data streams
   - Linux/macOS use extended attributes
3. Dropbox recognizes this attribute consistently across all platforms, regardless of which script set it

This means you can:

- Run the PowerShell script when using your Dropbox on Windows
- Run the Bash script when using your Dropbox on Linux/macOS
- Switch between operating systems freely without conflicts

After running either script, remember to restart Dropbox for the changes to take effect.
