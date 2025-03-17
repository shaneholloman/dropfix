# Dropbox Ignore Pattern Configuration Guide

## Method 1: Using .dropboxignore (Professional/Business Accounts Only)

Create a `.dropboxignore` file in your Dropbox root folder:

```txt
.venv/
.venv/**
.conda/
.conda/**
```

## Method 2: PowerShell Command (Windows)

### Personal Accounts Windows

```powershell
Set-Content -Path "$env:LOCALAPPDATA\Dropbox\instance1\sync_exclude_list" -Value ".venv`n.venv/**"
```

### Business Accounts Windows

```powershell
Set-Content -Path "$env:LOCALAPPDATA\Dropbox\host.db\business\sync_exclude_list" -Value ".venv`n.venv/**"
```

## Method 3: Terminal Command (macOS/Linux)

### Personal Accounts Unix

```bash
echo -e ".venv\n.venv/**" > ~/.dropbox/instance1/sync_exclude_list
```

### Business Accounts Unix

```bash
echo -e ".venv\n.venv/**" > ~/.dropbox/host.db/business/sync_exclude_list
```

## Method 4: Individual File/Directory Ignoring

### Windows (using NTFS streams)

To ignore a specific file or directory:

```powershell
Set-Content -Path 'C:\Users\shane\Dropbox\path\to\file.ext' -Stream com.dropbox.ignored -Value 1
```

### macOS (using extended attributes)

To ignore a specific file or directory:

```bash
xattr -w com.dropbox.ignored 1 '/Users/yourname/Dropbox/path/to/file.ext'
```

### Linux (using attributes)

To ignore a specific file or directory:

```bash
attr -s com.dropbox.ignored -V 1 '/home/yourname/Dropbox/path/to/file.ext'
```

All three methods:

- Uses NTFS alternate data streams
- Works for both individual files AND directories
- When used on a directory, automatically ignores ALL contents recursively
- Can be useful for one-off ignores without modifying global patterns
- Works on both Personal and Business accounts
- Changes take effect immediately after setting the stream

Example for ignoring a directory:

```powershell
Set-Content -Path 'C:\Users\shane\Dropbox\path\to\folder' -Stream com.dropbox.ignored -Value 1
```

To find and ignore all directories with a specific name:

```powershell
# Ignore all .venv directories
Get-ChildItem -Path 'C:\Users\shane\Dropbox' -Directory -Recurse -Filter ".venv" |
    ForEach-Object { Set-Content -Path $_.FullName -Stream com.dropbox.ignored -Value 1 }

# Ignore all .conda directories
Get-ChildItem -Path 'C:\Users\shane\Dropbox' -Directory -Recurse -Filter ".conda" |
    ForEach-Object { Set-Content -Path $_.FullName -Stream com.dropbox.ignored -Value 1 }

# Ignore all node_modules directories
Get-ChildItem -Path 'C:\Users\shane\Dropbox' -Directory -Recurse -Filter "node_modules" |
    ForEach-Object { Set-Content -Path $_.FullName -Stream com.dropbox.ignored -Value 1 }
```

And for bulk operations on macOS:

```bash
# Ignore all .venv directories
find ~/Dropbox -type d -name ".venv" -exec xattr -w com.dropbox.ignored 1 {} \;

# Ignore all .conda directories
find ~/Dropbox -type d -name ".conda" -exec xattr -w com.dropbox.ignored 1 {} \;

# Ignore all .venv directories
find ~/Dropbox -type d -name ".venv" -exec attr -s com.dropbox.ignored -V 1 {} \;

# Ignore all .conda directories
find ~/Dropbox -type d -name ".conda" -exec attr -s com.dropbox.ignored -V 1 {} \;

# Ignore all node_modules directories
find ~/Dropbox -type d -name "node_modules" -exec attr -s com.dropbox.ignored -V 1 {} \;
```

## Notes

- Restart Dropbox after making any changes
- For personal accounts without .dropboxignore support, you can also use Selective Sync in the Dropbox desktop app settings
- These patterns will ignore all `.venv` directories and their contents
- The instance number may vary: If you have multiple Dropbox installations or have reinstalled Dropbox, the path might be `instance2`, `instance3`, etc. instead of `instance1`. Check your local Dropbox directory to find the correct instance number
- On Windows, check: `%LOCALAPPDATA%\Dropbox\`
- On macOS/Linux, check: `~/.dropbox/`
- For Business accounts, make sure you're logged in with your business account when applying these changes
