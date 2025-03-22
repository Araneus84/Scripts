param (
    [Parameter(Mandatory = $true)]
    [string[]]$FolderPath,
    
    [Parameter(Mandatory = $false)]
    [string]$OutputFile,
    
    [Parameter(Mandatory = $false)]
    [ValidateSet("MD5", "SHA1", "SHA256", "SHA384", "SHA512")]
    [string]$Algorithm = "SHA256"
)

# Function to get file hash
function Get-FileHashSafe {
    param (
        [string]$FilePath,
        [string]$Algorithm
    )
    
    try {
        return Get-FileHash -Path $FilePath -Algorithm $Algorithm
    }
    catch {
        Write-Warning "Could not hash file: $FilePath - $_"
        return $null
    }
}

# Validate folder paths
foreach ($path in $FolderPath) {
    if (-not (Test-Path -Path $path -PathType Container)) {
        Write-Error "Folder path does not exist or is not a directory: $path"
        exit 1
    }
}

Write-Host "Scanning for files..." -ForegroundColor Cyan
$allFiles = @()
foreach ($path in $FolderPath) {
    $files = Get-ChildItem -Path $path -Recurse -File
    $allFiles += $files
    Write-Host "Found $($files.Count) files in $path" -ForegroundColor Gray
}

Write-Host "Found a total of $($allFiles.Count) files to process" -ForegroundColor Cyan
Write-Host "Calculating file hashes using $Algorithm algorithm..." -ForegroundColor Cyan

# Calculate progress parameters
$totalFiles = $allFiles.Count
$processedFiles = 0
$startTime = Get-Date

# Calculate hashes for all files
$fileHashes = @{}
foreach ($file in $allFiles) {
    # Update progress
    $processedFiles++
    $percentComplete = [math]::Round(($processedFiles / $totalFiles) * 100, 2)
    
    # Calculate ETA
    $elapsedTime = (Get-Date) - $startTime
    $estimatedTotalTime = $elapsedTime.TotalSeconds / $percentComplete * 100
    $remainingTime = $estimatedTotalTime - $elapsedTime.TotalSeconds
    $eta = [timespan]::FromSeconds($remainingTime)
    
    Write-Progress -Activity "Calculating file hashes" -Status "$percentComplete% Complete" -PercentComplete $percentComplete -CurrentOperation "Processing $($file.FullName)" -SecondsRemaining $remainingTime
    
    # Calculate hash
    $hash = Get-FileHashSafe -FilePath $file.FullName -Algorithm $Algorithm
    
    if ($hash) {
        if (-not $fileHashes.ContainsKey($hash.Hash)) {
            $fileHashes[$hash.Hash] = @()
        }
        $fileHashes[$hash.Hash] += $file.FullName
    }
}

Write-Progress -Activity "Calculating file hashes" -Completed

# Find duplicates
$duplicates = $fileHashes.GetEnumerator() | Where-Object { $_.Value.Count -gt 1 }
$duplicateCount = $duplicates.Count

Write-Host "Found $duplicateCount sets of duplicate files" -ForegroundColor Green

# Prepare output
$output = @()
$output += "Duplicate Files Report"
$output += "======================="
$output += "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$output += "Scanned Folders: $($FolderPath -join ', ')"
$output += "Hash Algorithm: $Algorithm"
$output += "Total Files Scanned: $totalFiles"
$output += "Duplicate Sets Found: $duplicateCount"
$output += ""

if ($duplicateCount -gt 0) {
    $duplicateFileCount = 0
    $wastedSpace = 0
    
    $i = 1
    foreach ($duplicate in $duplicates) {
        $files = $duplicate.Value
        $duplicateFileCount += ($files.Count - 1)
        
        # Calculate wasted space (size of all duplicates except one original)
        $fileSize = (Get-Item -Path $files[0]).Length
        $wastedSpace += $fileSize * ($files.Count - 1)
        
        $output += "Duplicate Set #$i (Hash: $($duplicate.Key))"
        $output += "----------------------------------------"
        foreach ($file in $files) {
            $fileObj = Get-Item -Path $file
            $output += "  $file ($('{0:N2}' -f ($fileObj.Length / 1MB)) MB, Modified: $($fileObj.LastWriteTime))"
        }
        $output += ""
        $i++
    }
    
    $output += "Summary:"
    $output += "  Total duplicate files: $duplicateFileCount"
    $output += "  Wasted space: $('{0:N2}' -f ($wastedSpace / 1MB)) MB ($('{0:N2}' -f ($wastedSpace / 1GB)) GB)"
}
else {
    $output += "No duplicate files found."
}

# Output results
if ($OutputFile) {
    $output | Out-File -FilePath $OutputFile -Encoding utf8
    Write-Host "Results saved to $OutputFile" -ForegroundColor Green
}
else {
    $output | ForEach-Object { Write-Host $_ }
}
