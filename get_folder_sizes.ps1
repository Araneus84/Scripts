param (
    [Parameter(Mandatory = $false)]
    [string]$FolderPath = (Get-Location).Path,
    
    [Parameter(Mandatory = $false)]
    [int]$Depth = 1,
    
    [Parameter(Mandatory = $false)]
    [bool]$SortBySize = $true,
    
    [Parameter(Mandatory = $false)]
    [int]$Top = 0,
    
    [Parameter(Mandatory = $false)]
    [bool]$IncludeFiles = $false
)

# Function to convert bytes to human-readable format
function Format-FileSize {
    param ([long]$Size)
    
    if ($Size -ge 1TB) { return "{0:N2} TB" -f ($Size / 1TB) }
    elseif ($Size -ge 1GB) { return "{0:N2} GB" -f ($Size / 1GB) }
    elseif ($Size -ge 1MB) { return "{0:N2} MB" -f ($Size / 1MB) }
    elseif ($Size -ge 1KB) { return "{0:N2} KB" -f ($Size / 1KB) }
    else { return "$Size Bytes" }
}

# Verify the folder path exists
if (-not (Test-Path -Path $FolderPath -PathType Container)) {
    Write-Error "Folder path does not exist: $FolderPath"
    exit 1
}

Write-Host "Calculating folder sizes for: $FolderPath" -ForegroundColor Cyan
Write-Host "This may take some time depending on the number and size of folders..." -ForegroundColor Yellow

# Function to recursively get folder size
function Get-FolderSize {
    param (
        [string]$Path,
        [int]$CurrentDepth = 0,
        [int]$MaxDepth = 1
    )
    
    $size = 0
    
    # Get all items in the current folder
    try {
        $items = Get-ChildItem -Path $Path -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Warning "Could not access: $Path - $_"
        return 0
    }
    
    # Calculate size of all files in the current folder
    $files = $items | Where-Object { -not $_.PSIsContainer }
    foreach ($file in $files) {
        $size += $file.Length
    }
    
    # If we haven't reached max depth, process subfolders
    if ($CurrentDepth -lt $MaxDepth) {
        $folders = $items | Where-Object { $_.PSIsContainer }
        foreach ($folder in $folders) {
            $size += Get-FolderSize -Path $folder.FullName -CurrentDepth ($CurrentDepth + 1) -MaxDepth $MaxDepth
        }
    }
    
    return $size
}

# Get items to analyze
$items = @()

# Get subfolders
$folders = Get-ChildItem -Path $FolderPath -Directory -Force -ErrorAction SilentlyContinue

# Process each folder
$totalFolders = $folders.Count
$processedFolders = 0
$results = @()

foreach ($folder in $folders) {
    $processedFolders++
    $percentComplete = [math]::Round(($processedFolders / $totalFolders) * 100, 2)
    
    Write-Progress -Activity "Calculating folder sizes" -Status "$percentComplete% Complete" -PercentComplete $percentComplete -CurrentOperation "Processing $($folder.FullName)"
    
    $size = Get-FolderSize -Path $folder.FullName -MaxDepth $Depth
    $results += [PSCustomObject]@{
        Name              = $folder.Name
        Path              = $folder.FullName
        Size              = $size
        HumanReadableSize = Format-FileSize -Size $size
        Type              = "Folder"
    }
}

# Include files in the root folder if requested
if ($IncludeFiles) {
    $files = Get-ChildItem -Path $FolderPath -File -Force -ErrorAction SilentlyContinue
    foreach ($file in $files) {
        $results += [PSCustomObject]@{
            Name              = $file.Name
            Path              = $file.FullName
            Size              = $file.Length
            HumanReadableSize = Format-FileSize -Size $file.Length
            Type              = "File"
        }
    }
}

Write-Progress -Activity "Calculating folder sizes" -Completed

# Sort results if requested
if ($SortBySize) {
    $results = $results | Sort-Object -Property Size -Descending
}

# Limit results if requested
if ($Top -gt 0 -and $results.Count -gt $Top) {
    $results = $results | Select-Object -First $Top
}

# Calculate total size
$totalSize = ($results | Measure-Object -Property Size -Sum).Sum
$totalHumanReadable = Format-FileSize -Size $totalSize

# Display results
Write-Host "`nFolder Size Report for: $FolderPath" -ForegroundColor Green
Write-Host "Total Size: $totalHumanReadable" -ForegroundColor Green
Write-Host "Items: $($results.Count)" -ForegroundColor Green
Write-Host "=" * 80

$results | Format-Table -Property Name, HumanReadableSize, Type, Path -AutoSize

# Optional: Export to CSV
# $results | Export-Csv -Path "FolderSizes.csv" -NoTypeInformation
