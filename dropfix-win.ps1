# Directories to ignore
$dirsToIgnore = @('.venv', '.conda', 'node_modules')
$dropboxPath = 'C:\Users\shane\Dropbox'

# Initialize counters
$totalProcessed = 0
$errors = @()

Write-Host "`nStarting Dropbox directory ignore process...`n" -ForegroundColor Cyan

foreach ($dirName in $dirsToIgnore) {
    Write-Host "Searching for '$dirName' directories..." -ForegroundColor Yellow

    # Get all matching directories
    $directories = Get-ChildItem -Path $dropboxPath -Directory -Recurse -Filter $dirName -ErrorAction SilentlyContinue
    $dirCount = ($directories | Measure-Object).Count

    if ($dirCount -eq 0) {
        Write-Host "No '$dirName' directories found.`n" -ForegroundColor Gray
        continue
    }

    Write-Host "Found $dirCount '$dirName' directories to process.`n" -ForegroundColor Green

    # Process each directory with progress bar
    $i = 0
    foreach ($dir in $directories) {
        $i++
        $percentComplete = ($i / $dirCount) * 100

        # Update progress bar
        $statusMessage = "Processing " + $i + " of " + $dirCount + ": " + $dir.FullName
        Write-Progress -Activity "Ignoring '$dirName' directories" -Status $statusMessage -PercentComplete $percentComplete

        try {
            Set-Content -Path $dir.FullName -Stream com.dropbox.ignored -Value 1 -ErrorAction Stop
            $totalProcessed++
        }
        catch {
            $errors += "Failed to ignore $($dir.FullName): $_"
        }
    }

    Write-Progress -Activity "Ignoring '$dirName' directories" -Completed
    Write-Host "Completed processing '$dirName' directories.`n" -ForegroundColor Green
}

# Final summary
Write-Host "Process completed!" -ForegroundColor Cyan
Write-Host "Total directories processed: $totalProcessed" -ForegroundColor Green

if ($errors.Count -gt 0) {
    Write-Host "`nErrors encountered:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host "- $_" -ForegroundColor Red }
}

Write-Host "`nNote: You may need to restart Dropbox for changes to take effect." -ForegroundColor Yellow
