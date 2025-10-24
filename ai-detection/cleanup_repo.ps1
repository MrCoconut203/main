<#
PowerShell cleanup script for ai-detection repo.
Will remove: build logs, temp sample images, empty scripts folder.
By default it WILL NOT remove model files; pass -RemoveDuplicateModel to remove the duplicate model at repository root.
#>
param(
    [switch]$RemoveDuplicateModel
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Repository root: $repoRoot"

$targets = @(
    Join-Path $repoRoot 'build-plain.log',
    Join-Path $repoRoot 'web-last.log'
)

# Add all files in temp folder
$tempFolder = Join-Path $repoRoot 'temp'
if (Test-Path $tempFolder) {
    $tempFiles = Get-ChildItem -Path $tempFolder -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
    $targets += $tempFiles
}

# scripts folder (delete if empty)
$scriptsFolder = Join-Path $repoRoot 'scripts'
if (Test-Path $scriptsFolder) {
    $scriptFiles = Get-ChildItem -Path $scriptsFolder -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
    if ($scriptFiles.Count -eq 0) {
        $targets += $scriptsFolder
    } else {
        $targets += $scriptFiles
    }
}

# Duplicate model at repo root (not in ai-detection) -- optional
$rootModel = Join-Path (Split-Path $repoRoot -Parent) 'models\yolov8s.pt'
if ($RemoveDuplicateModel -and (Test-Path $rootModel)) {
    $targets += $rootModel
}

if ($targets.Count -eq 0) {
    Write-Host "No candidate files found for cleanup."
    exit 0
}

Write-Host "The following files/directories will be removed:" -ForegroundColor Yellow
$targets | ForEach-Object { Write-Host " - $_" }

$confirm = Read-Host "Proceed and delete these files? (y/N)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "Aborted by user. No files deleted."
    exit 0
}

foreach ($t in $targets) {
    try {
        if (Test-Path $t) {
            if ((Get-Item $t).PSIsContainer) {
                Remove-Item -Recurse -Force -Path $t
                Write-Host "Removed directory: $t"
            } else {
                Remove-Item -Force -Path $t
                Write-Host "Removed file: $t"
            }
        }
    } catch {
        Write-Warning "Failed to remove $t : $_"
    }
}

Write-Host "Cleanup completed." -ForegroundColor Green
