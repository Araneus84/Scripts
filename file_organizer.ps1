param (
    [Parameter(Mandatory = $true)]
    [string]$SourcePath,
    
    [Parameter(Mandatory = $false)]
    [string]$DestinationPath = $SourcePath
)

# Ensure paths end with a backslash
if (-not $SourcePath.EndsWith('\')) { $SourcePath += '\' }
if (-not $DestinationPath.EndsWith('\')) { $DestinationPath += '\' }

# Verify the source path exists
if (-not (Test-Path -Path $SourcePath)) {
    Write-Error "Source path does not exist: $SourcePath"
    exit 1
}

# Create the destination path if it doesn't exist
if (-not (Test-Path -Path $DestinationPath)) {
    New-Item -Path $DestinationPath -ItemType Directory -Force | Out-Null
    Write-Host "Created destination directory: $DestinationPath"
}

# Get all files recursively from the source path
$files = Get-ChildItem -Path $SourcePath -Recurse -File

# Process each file
foreach ($file in $files) {
    # Get the last modified year
    $year = $file.LastWriteTime.Year.ToString()
    
    # Create the year folder if it doesn't exist
    $yearFolder = Join-Path -Path $DestinationPath -ChildPath $year
    if (-not (Test-Path -Path $yearFolder)) {
        New-Item -Path $yearFolder -ItemType Directory -Force | Out-Null
        Write-Host "Created year directory: $yearFolder"
    }
    
    # Get the relative path of the file from the source root
    $relativePath = $file.FullName.Substring($SourcePath.Length)
    $relativeDir = [System.IO.Path]::GetDirectoryName($relativePath)
    
    # If the file is in a subfolder, create the same structure in the year folder
    if ($relativeDir) {
        $targetDir = Join-Path -Path $yearFolder -ChildPath $relativeDir
        if (-not (Test-Path -Path $targetDir)) {
            New-Item -Path $targetDir -ItemType Directory -Force | Out-Null
            Write-Host "Created directory structure: $targetDir"
        }
    }
    else {
        $targetDir = $yearFolder
    }
    
    # Construct the destination file path
    $destFile = Join-Path -Path $targetDir -ChildPath $file.Name
    
    # Check if the destination file already exists
    if (Test-Path -Path $destFile) {
        Write-Warning "File already exists at destination: $destFile"
        continue
    }
    
    # Move the file
    try {
        Move-Item -Path $file.FullName -Destination $destFile -ErrorAction Stop
        Write-Host "Moved: $($file.FullName) -> $destFile"
    }
    catch {
        Write-Error "Failed to move file $($file.FullName): $_"
    }
}

Write-Host "File organization complete!" -ForegroundColor Green
