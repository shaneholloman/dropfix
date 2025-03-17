# Dropfix: Advanced Dropbox Ignore Tools

This guide provides detailed methods for configuring Dropbox to ignore specific files and directories using Dropfix. For basic setup using our scripts, see the [main README](./README.md).

## Method 1: Using `.dropboxignore` (Business/Professional Accounts Only)

Create a `.dropboxignore` file in your Dropbox root folder:

```txt
.venv/
.venv/**
.conda/
.conda/**
node_modules/
node_modules/**
```

## Method 2: Using Sync Exclude Lists

### Windows (PowerShell)

```powershell
# Personal Account
Set-Content -Path "$env:LOCALAPPDATA\Dropbox\instance1\sync_exclude_list" -Value ".venv`n.venv/**`n.conda`n.conda/**`nnode_modules`nnode_modules/**"

# Business Account
Set-Content -Path "$env:LOCALAPPDATA\Dropbox\host.db\business\sync_exclude_list" -Value ".venv`n.venv/**`n.conda`n.conda/**`nnode_modules`nnode_modules/**"
```

### macOS/Linux (Bash)

```bash
# Personal Account
echo -e ".venv\n.venv/**\n.conda\n.conda/**\nnode_modules\nnode_modules/**" > ~/.dropbox/instance1/sync_exclude_list

# Business Account
echo -e ".venv\n.venv/**\n.conda\n.conda/**\nnode_modules\nnode_modules/**" > ~/.dropbox/host.db/business/sync_exclude_list
```

> **Note**: The instance number may vary. Check your local Dropbox directory for the correct instance number.

## Method 3: Setting Attributes on Individual Files/Directories

These commands manually set the Dropbox ignore attribute and are the basis for our provided scripts.

### Windows

```powershell
# Individual file/directory
Set-Content -Path "C:\Users\username\Dropbox\path\to\folder" -Stream com.dropbox.ignored -Value 1

# Bulk operation - all .venv directories
Get-ChildItem -Path "C:\Users\username\Dropbox" -Directory -Recurse -Filter ".venv" |
    ForEach-Object { Set-Content -Path $_.FullName -Stream com.dropbox.ignored -Value 1 }
```

### macOS

```bash
# Individual file/directory
xattr -w com.dropbox.ignored 1 "/Users/username/Dropbox/path/to/folder"

# Bulk operation - all .venv directories
find ~/Dropbox -type d -name ".venv" -exec xattr -w com.dropbox.ignored 1 {} \;
```

### Linux

```bash
# Individual file/directory
attr -s com.dropbox.ignored -V 1 "/home/username/Dropbox/path/to/folder"

# Bulk operation - all .venv directories
find ~/Dropbox -type d -name ".venv" -exec attr -s com.dropbox.ignored -V 1 {} \;
```

## Attribute Method Benefits

- Works on all Dropbox account types (Personal and Business)
- Platform-agnostic (the attribute is recognized across all operating systems)
- Applies recursively when set on directories
- Works for individual files and directories
- Takes effect immediately after setting (though restarting Dropbox is recommended)

## Important Notes

- Always restart Dropbox after making changes
- For personal accounts without `.dropboxignore` support, you can also use Selective Sync in the Dropbox desktop app settings
- When using sync exclude lists, always include both the directory name and `/**` pattern to ignore all contents
- Replace username in paths with your actual username

## About Code Examples

The examples in this guide and the related scripts use hardcoded paths for simplicity:

- Windows examples use `C:\Users\username\Dropbox` or `C:\Users\shane\Dropbox`
- macOS examples use `/Users/username/Dropbox` or `~/Dropbox`
- Linux examples use `/home/username/Dropbox` or `~/Dropbox`

These were originally created for personal use, so paths were hardcoded to avoid configuration steps. When using these commands or scripts, make sure to update the paths to match your specific Dropbox location.
