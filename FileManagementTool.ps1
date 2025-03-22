Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Get the script directory to locate the other scripts
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$fileOrganizerPath = Join-Path -Path $scriptPath -ChildPath "file_organizer.ps1"
$findDuplicatesPath = Join-Path -Path $scriptPath -ChildPath "find_duplicates.ps1"
$getFolderSizesPath = Join-Path -Path $scriptPath -ChildPath "get_folder_sizes.ps1"

# Verify that all required scripts exist
$missingScripts = @()
if (-not (Test-Path $fileOrganizerPath)) { $missingScripts += "file_organizer.ps1" }
if (-not (Test-Path $findDuplicatesPath)) { $missingScripts += "find_duplicates.ps1" }
if (-not (Test-Path $getFolderSizesPath)) { $missingScripts += "get_folder_sizes.ps1" }

if ($missingScripts.Count -gt 0) {
    [System.Windows.Forms.MessageBox]::Show(
        "The following required scripts are missing:`n`n" + ($missingScripts -join "`n") + 
        "`n`nPlease make sure these scripts are in the same directory as this tool.",
        "Missing Scripts",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
    exit
}

# Create the main form
$form = New-Object System.Windows.Forms.Form
$form.Text = "File Management Tool"
$form.Size = New-Object System.Drawing.Size(800, 700)
$form.StartPosition = "CenterScreen"
$form.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$form.Icon = [System.Drawing.SystemIcons]::Application

# Create tab control
$tabControl = New-Object System.Windows.Forms.TabControl
$tabControl.Dock = [System.Windows.Forms.DockStyle]::Fill
$form.Controls.Add($tabControl)

# Create tabs
$tabOrganizer = New-Object System.Windows.Forms.TabPage
$tabOrganizer.Text = "File Organizer"
$tabControl.Controls.Add($tabOrganizer)

$tabDuplicates = New-Object System.Windows.Forms.TabPage
$tabDuplicates.Text = "Duplicate Finder"
$tabControl.Controls.Add($tabDuplicates)

$tabSizes = New-Object System.Windows.Forms.TabPage
$tabSizes.Text = "Folder Size Analyzer"
$tabControl.Controls.Add($tabSizes)

# Status strip for showing progress and messages
$statusStrip = New-Object System.Windows.Forms.StatusStrip
$statusLabel = New-Object System.Windows.Forms.ToolStripStatusLabel
$statusLabel.Text = "Ready"
$statusStrip.Items.Add($statusLabel)
$form.Controls.Add($statusStrip)

# Function to create a folder browser button and textbox
function New-FolderBrowserControl {
    param (
        [System.Windows.Forms.Control]$Parent,
        [string]$Label,
        [int]$Y,
        [scriptblock]$OnSelected = $null
    )
    
    $label = New-Object System.Windows.Forms.Label
    $label.Text = "$Label"
    $label.Location = New-Object System.Drawing.Point(20, $Y)
    $label.Size = New-Object System.Drawing.Size(120, 23)
    $Parent.Controls.Add($label)
    
    $textBox = New-Object System.Windows.Forms.TextBox
    $textBox.Location = New-Object System.Drawing.Point(150, $Y)
    $textBox.Size = New-Object System.Drawing.Size(450, 23)
    $textBox.Anchor = [System.Windows.Forms.AnchorStyles]::Left -bor [System.Windows.Forms.AnchorStyles]::Right -bor [System.Windows.Forms.AnchorStyles]::Top
    $Parent.Controls.Add($textBox)
    
    $button = New-Object System.Windows.Forms.Button
    $button.Text = "Browse..."
    $button.Location = New-Object System.Drawing.Point(610, $Y)
    $button.Size = New-Object System.Drawing.Size(100, 28)
    $button.Anchor = [System.Windows.Forms.AnchorStyles]::Right -bor [System.Windows.Forms.AnchorStyles]::Top
    $Parent.Controls.Add($button)
    
    $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderBrowser.Description = "Select a folder"
    
    $button.Add_Click({
            if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
                $textBox.Text = $folderBrowser.SelectedPath
                if ($null -ne $OnSelected) {
                    & $OnSelected $folderBrowser.SelectedPath
                }
            }
        })
    
    return $textBox
}#region File Organizer Tab# Source folder
$txtOrganizerSource = New-FolderBrowserControl -Parent $tabOrganizer -Label "Source Folder:" -Y 30

# Destination folder
$lblOrganizerDest = New-Object System.Windows.Forms.Label
$lblOrganizerDest.Text = "Destination Folder:"
$lblOrganizerDest.Location = New-Object System.Drawing.Point(20, 70)
$lblOrganizerDest.Size = New-Object System.Drawing.Size(120, 23)
$tabOrganizer.Controls.Add($lblOrganizerDest)

$txtOrganizerDest = New-Object System.Windows.Forms.TextBox
$txtOrganizerDest.Location = New-Object System.Drawing.Point(150, 70)
$txtOrganizerDest.Size = New-Object System.Drawing.Size(450, 23)
$txtOrganizerDest.Anchor = [System.Windows.Forms.AnchorStyles]::Left -bor [System.Windows.Forms.AnchorStyles]::Right -bor [System.Windows.Forms.AnchorStyles]::Top
$tabOrganizer.Controls.Add($txtOrganizerDest)

$btnOrganizerDest = New-Object System.Windows.Forms.Button
$btnOrganizerDest.Text = "Browse..."
$btnOrganizerDest.Location = New-Object System.Drawing.Point(610, 68)
$btnOrganizerDest.Size = New-Object System.Drawing.Size(100, 28)
$btnOrganizerDest.Anchor = [System.Windows.Forms.AnchorStyles]::Right -bor [System.Windows.Forms.AnchorStyles]::Top
$tabOrganizer.Controls.Add($btnOrganizerDest)

$folderBrowserDest = New-Object System.Windows.Forms.FolderBrowserDialog
$folderBrowserDest.Description = "Select destination folder"

$btnOrganizerDest.Add_Click({
        if ($folderBrowserDest.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            $txtOrganizerDest.Text = $folderBrowserDest.SelectedPath
        }
    })

# Same location checkbox
$chkSameLocation = New-Object System.Windows.Forms.CheckBox
$chkSameLocation.Text = "Use source folder as destination"
$chkSameLocation.Location = New-Object System.Drawing.Point(150, 100)
$chkSameLocation.Size = New-Object System.Drawing.Size(250, 23)
$chkSameLocation.Checked = $true
$tabOrganizer.Controls.Add($chkSameLocation)

$chkSameLocation.Add_CheckedChanged({
        $txtOrganizerDest.Enabled = -not $chkSameLocation.Checked
        $btnOrganizerDest.Enabled = -not $chkSameLocation.Checked
        if ($chkSameLocation.Checked) {
            $txtOrganizerDest.Text = $txtOrganizerSource.Text
        }
    })

# Organize button
$btnOrganize = New-Object System.Windows.Forms.Button
$btnOrganize.Text = "Organize Files"
$btnOrganize.Location = New-Object System.Drawing.Point(150, 140)
$btnOrganize.Size = New-Object System.Drawing.Size(150, 35)
$tabOrganizer.Controls.Add($btnOrganize)

# Results textbox
$txtOrganizerResults = New-Object System.Windows.Forms.TextBox
$txtOrganizerResults.Location = New-Object System.Drawing.Point(20, 190)
$txtOrganizerResults.Size = New-Object System.Drawing.Size(730, 400)
$txtOrganizerResults.Multiline = $true
$txtOrganizerResults.ScrollBars = "Vertical"
$txtOrganizerResults.ReadOnly = $true
$txtOrganizerResults.Font = New-Object System.Drawing.Font("Consolas", 9)
$txtOrganizerResults.Anchor = [System.Windows.Forms.AnchorStyles]::Top -bor [System.Windows.Forms.AnchorStyles]::Bottom -bor [System.Windows.Forms.AnchorStyles]::Left -bor [System.Windows.Forms.AnchorStyles]::Right
$tabOrganizer.Controls.Add($txtOrganizerResults)

# Organize files function
$btnOrganize.Add_Click({
        $sourcePath = $txtOrganizerSource.Text
        $destinationPath = if ($chkSameLocation.Checked) { $sourcePath } else { $txtOrganizerDest.Text }
    
        if (-not $sourcePath) {
            [System.Windows.Forms.MessageBox]::Show("Please select a source folder.", "Missing Information", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
            return
        }
    
        $txtOrganizerResults.Clear()
        $txtOrganizerResults.AppendText("Starting file organization...`r`n")
        $txtOrganizerResults.AppendText("Source: $sourcePath`r`n")
        $txtOrganizerResults.AppendText("Destination: $destinationPath`r`n`r`n")
    
        $statusLabel.Text = "Organizing files..."
    
        # Create a PowerShell process to run the file_organizer.ps1 script
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo.FileName = "powershell.exe"
        $process.StartInfo.Arguments = "-ExecutionPolicy Bypass -File `"$fileOrganizerPath`" -SourcePath `"$sourcePath`" -DestinationPath `"$destinationPath`""
        $process.StartInfo.UseShellExecute = $false
        $process.StartInfo.RedirectStandardOutput = $true
        $process.StartInfo.RedirectStandardError = $true
        $process.StartInfo.CreateNoWindow = $true
    
        $outputBuilder = New-Object System.Text.StringBuilder
        $errorBuilder = New-Object System.Text.StringBuilder
    
        $outputHandler = [System.EventHandler[System.Diagnostics.DataReceivedEventArgs]] {
            if (-not [String]::IsNullOrEmpty($EventArgs.Data)) {
                $outputBuilder.AppendLine($EventArgs.Data)
                $txtOrganizerResults.AppendText($EventArgs.Data + "`r`n")
                $txtOrganizerResults.ScrollToCaret()
                [System.Windows.Forms.Application]::DoEvents()
            }
        }
    
        $errorHandler = [System.EventHandler[System.Diagnostics.DataReceivedEventArgs]] {
            if (-not [String]::IsNullOrEmpty($EventArgs.Data)) {
                $errorBuilder.AppendLine($EventArgs.Data)
                $txtOrganizerResults.AppendText("ERROR: " + $EventArgs.Data + "`r`n")
                $txtOrganizerResults.ScrollToCaret()
                [System.Windows.Forms.Application]::DoEvents()
            }
        }
    
        $process.OutputDataReceived += $outputHandler
        $process.ErrorDataReceived += $errorHandler
    
        $process.Start() | Out-Null
        $process.BeginOutputReadLine()
        $process.BeginErrorReadLine()
        $process.WaitForExit()
    
        $txtOrganizerResults.AppendText("`r`nFile organization complete!`r`n")
        $statusLabel.Text = "File organization complete."
    })
#endregion

#region Duplicate Finder Tab
# Folder selection panel
$panelDupFolders = New-Object System.Windows.Forms.Panel
$panelDupFolders.Location = New-Object System.Drawing.Point(20, 20)
$panelDupFolders.Size = New-Object System.Drawing.Size(730, 120)
$panelDupFolders.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
$tabDuplicates.Controls.Add($panelDupFolders)

# Folder list
$lblDupFolders = New-Object System.Windows.Forms.Label
$lblDupFolders.Text = "Folders to scan:"
$lblDupFolders.Location = New-Object System.Drawing.Point(10, 10)
$lblDupFolders.Size = New-Object System.Drawing.Size(150, 23)
$panelDupFolders.Controls.Add($lblDupFolders)

$listDupFolders = New-Object System.Windows.Forms.ListBox
$listDupFolders.Location = New-Object System.Drawing.Point(10, 35)
$listDupFolders.Size = New-Object System.Drawing.Size(500, 70)
$listDupFolders.SelectionMode = [System.Windows.Forms.SelectionMode]::One
$panelDupFolders.Controls.Add($listDupFolders)

# Add folder button
$btnDupAddFolder = New-Object System.Windows.Forms.Button
$btnDupAddFolder.Text = "Add Folder"
$btnDupAddFolder.Location = New-Object System.Drawing.Point(520, 35)
$btnDupAddFolder.Size = New-Object System.Drawing.Size(100, 30)
$panelDupFolders.Controls.Add($btnDupAddFolder)
# Remove folder button
$btnDupRemoveFolder = New-Object System.Windows.Forms.Button
$btnDupRemoveFolder.Text = "Remove Folder"
$btnDupRemoveFolder.Location = New-Object System.Drawing.Point(520, 75)
$btnDupRemoveFolder.Size = New-Object System.Drawing.Size(100, 30)
$btnDupRemoveFolder.Enabled = $false
$panelDupFolders.Controls.Add($btnDupRemoveFolder)

# Add folder event
$folderBrowserDup = New-Object System.Windows.Forms.FolderBrowserDialog
$folderBrowserDup.Description = "Select a folder to scan for duplicates"

$btnDupAddFolder.Add_Click({
        if ($folderBrowserDup.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            $path = $folderBrowserDup.SelectedPath
            if (-not $listDupFolders.Items.Contains($path)) {
                $listDupFolders.Items.Add($path)
            }
        }
    })

# Remove folder event
$btnDupRemoveFolder.Add_Click({
        if ($listDupFolders.SelectedIndex -ge 0) {
            $listDupFolders.Items.RemoveAt($listDupFolders.SelectedIndex)
            $btnDupRemoveFolder.Enabled = $false
        }
    })

# Selection changed event
$listDupFolders.Add_SelectedIndexChanged({
        $btnDupRemoveFolder.Enabled = $listDupFolders.SelectedIndex -ge 0
    })

# Options panel
$panelDupOptions = New-Object System.Windows.Forms.Panel
$panelDupOptions.Location = New-Object System.Drawing.Point(20, 150)
$panelDupOptions.Size = New-Object System.Drawing.Size(730, 60)
$panelDupOptions.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
$tabDuplicates.Controls.Add($panelDupOptions)

# Hash algorithm
$lblDupAlgorithm = New-Object System.Windows.Forms.Label
$lblDupAlgorithm.Text = "Hash Algorithm:"
$lblDupAlgorithm.Location = New-Object System.Drawing.Point(10, 20)
$lblDupAlgorithm.Size = New-Object System.Drawing.Size(100, 23)
$panelDupOptions.Controls.Add($lblDupAlgorithm)

$comboDupAlgorithm = New-Object System.Windows.Forms.ComboBox
$comboDupAlgorithm.Location = New-Object System.Drawing.Point(120, 18)
$comboDupAlgorithm.Size = New-Object System.Drawing.Size(150, 23)
$comboDupAlgorithm.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList
$comboDupAlgorithm.Items.AddRange(@("MD5", "SHA1", "SHA256", "SHA384", "SHA512"))
$comboDupAlgorithm.SelectedIndex = 2  # Default to SHA256
$panelDupOptions.Controls.Add($comboDupAlgorithm)

# Output file option
$chkDupOutputFile = New-Object System.Windows.Forms.CheckBox
$chkDupOutputFile.Text = "Save results to file"
$chkDupOutputFile.Location = New-Object System.Drawing.Point(300, 18)
$chkDupOutputFile.Size = New-Object System.Drawing.Size(150, 23)
$panelDupOptions.Controls.Add($chkDupOutputFile)

# Find duplicates button
$btnFindDuplicates = New-Object System.Windows.Forms.Button
$btnFindDuplicates.Text = "Find Duplicates"
$btnFindDuplicates.Location = New-Object System.Drawing.Point(20, 220)
$btnFindDuplicates.Size = New-Object System.Drawing.Size(150, 35)
$tabDuplicates.Controls.Add($btnFindDuplicates)

# Results textbox
$txtDuplicatesResults = New-Object System.Windows.Forms.TextBox
$txtDuplicatesResults.Location = New-Object System.Drawing.Point(20, 270)
$txtDuplicatesResults.Size = New-Object System.Drawing.Size(730, 320)
$txtDuplicatesResults.Multiline = $true
$txtDuplicatesResults.ScrollBars = "Vertical"
$txtDuplicatesResults.ReadOnly = $true
$txtDuplicatesResults.Font = New-Object System.Drawing.Font("Consolas", 9)
$txtDuplicatesResults.Anchor = [System.Windows.Forms.AnchorStyles]::Top -bor [System.Windows.Forms.AnchorStyles]::Bottom -bor [System.Windows.Forms.AnchorStyles]::Left -bor [System.Windows.Forms.AnchorStyles]::Right
$tabDuplicates.Controls.Add($txtDuplicatesResults)

# Find duplicates function
$btnFindDuplicates.Add_Click({
        # Validate input
        if ($listDupFolders.Items.Count -eq 0) {
            [System.Windows.Forms.MessageBox]::Show("Please add at least one folder to scan.", "Missing Information", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
            return
        }
    
        $txtDuplicatesResults.Clear()
        $txtDuplicatesResults.AppendText("Starting duplicate file search...`r`n")
    
        # Build folder paths parameter
        $folderPaths = @()
        foreach ($folder in $listDupFolders.Items) {
            $folderPaths += "`"$folder`""
        }
        $folderPathsParam = $folderPaths -join ","
    
        # Get selected algorithm
        $algorithm = $comboDupAlgorithm.SelectedItem
    
        # Determine output file
        $outputFileParam = ""
        if ($chkDupOutputFile.Checked) {
            $saveFileDialog = New-Object System.Windows.Forms.SaveFileDialog
            $saveFileDialog.Filter = "Text files (*.txt)|*.txt|All files (*.*)|*.*"
            $saveFileDialog.DefaultExt = "txt"
            $saveFileDialog.Title = "Save Duplicate Files Report"
        
            if ($saveFileDialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
                $outputFileParam = "-OutputFile `"$($saveFileDialog.FileName)`""
            }
            else {
                $chkDupOutputFile.Checked = $false
            }
        }
    
        $statusLabel.Text = "Searching for duplicate files..."
    
        # Create a PowerShell process to run the find_duplicates.ps1 script
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo.FileName = "powershell.exe"
        $process.StartInfo.Arguments = "-ExecutionPolicy Bypass -File `"$findDuplicatesPath`" -FolderPath $folderPathsParam -Algorithm $algorithm $outputFileParam"
        $process.StartInfo.UseShellExecute = $false
        $process.StartInfo.RedirectStandardOutput = $true
        $process.StartInfo.RedirectStandardError = $true
        $process.StartInfo.CreateNoWindow = $true
    
        $outputBuilder = New-Object System.Text.StringBuilder
        $errorBuilder = New-Object System.Text.StringBuilder
    
        $outputHandler = [System.EventHandler[System.Diagnostics.DataReceivedEventArgs]] {
            if (-not [String]::IsNullOrEmpty($EventArgs.Data)) {
                $outputBuilder.AppendLine($EventArgs.Data)
                $txtDuplicatesResults.AppendText($EventArgs.Data + "`r`n")
                $txtDuplicatesResults.ScrollToCaret()
                [System.Windows.Forms.Application]::DoEvents()
            }
        }
    
        $errorHandler = [System.EventHandler[System.Diagnostics.DataReceivedEventArgs]] {
            if (-not [String]::IsNullOrEmpty($EventArgs.Data)) {
                $errorBuilder.AppendLine($EventArgs.Data)
                $txtDuplicatesResults.AppendText("ERROR: " + $EventArgs.Data + "`r`n")
                $txtDuplicatesResults.ScrollToCaret()
                [System.Windows.Forms.Application]::DoEvents()
            }
        }
    
        $process.OutputDataReceived += $outputHandler
        $process.ErrorDataReceived += $errorHandler
    
        $process.Start() | Out-Null
        $process.BeginOutputReadLine()
        $process.BeginErrorReadLine()
        $process.WaitForExit()
    
        $txtDuplicatesResults.AppendText("`r`nDuplicate file search complete!`r`n")
        $statusLabel.Text = "Duplicate file search complete."
    })
#endregion

#region Folder Size Analyzer Tab
# Folder selection
$txtSizesFolder = New-FolderBrowserControl -Parent $tabSizes -Label "Folder to analyze:" -Y 30

# Options panel
$panelSizesOptions = New-Object System.Windows.Forms.Panel
$panelSizesOptions.Location = New-Object System.Drawing.Point(20, 70)
$panelSizesOptions.Size = New-Object System.Drawing.Size(730, 100)
$panelSizesOptions.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
$tabSizes.Controls.Add($panelSizesOptions)

# Depth option
$lblSizesDepth = New-Object System.Windows.Forms.Label
$lblSizesDepth.Text = "Scan Depth:"
$lblSizesDepth.Location = New-Object System.Drawing.Point(10, 20)
$lblSizesDepth.Size = New-Object System.Drawing.Size(100, 23)
$panelSizesOptions.Controls.Add($lblSizesDepth)

$numSizesDepth = New-Object System.Windows.Forms.NumericUpDown
$numSizesDepth.Location = New-Object System.Drawing.Point(120, 18)
$numSizesDepth.Size = New-Object System.Drawing.Size(80, 23)
$numSizesDepth.Minimum = 1
$numSizesDepth.Maximum = 10
$numSizesDepth.Value = 1
$panelSizesOptions.Controls.Add($numSizesDepth)

# Sort by size option
$chkSizesSortBySize = New-Object System.Windows.Forms.CheckBox
$chkSizesSortBySize.Text = "Sort by size (descending)"
$chkSizesSortBySize.Location = New-Object System.Drawing.Point(10, 50)
$chkSizesSortBySize.Size = New-Object System.Drawing.Size(200, 23)
$chkSizesSortBySize.Checked = $true
$panelSizesOptions.Controls.Add($chkSizesSortBySize)

# Top N option
$lblSizesTop = New-Object System.Windows.Forms.Label
$lblSizesTop.Text = "Show Top:"
$lblSizesTop.Location = New-Object System.Drawing.Point(250, 20)
$lblSizesTop.Size = New-Object System.Drawing.Size(80, 23)
$panelSizesOptions.Controls.Add($lblSizesTop)

$numSizesTop = New-Object System.Windows.Forms.NumericUpDown
$numSizesTop.Location = New-Object System.Drawing.Point(330, 18)
$numSizesTop.Size = New-Object System.Drawing.Size(80, 23)
$numSizesTop.Minimum = 0
$numSizesTop.Maximum = 1000
$numSizesTop.Value = 0
$panelSizesOptions.Controls.Add($numSizesTop)

$lblSizesTopInfo = New-Object System.Windows.Forms.Label
$lblSizesTopInfo.Text = "(0 = show all)"
$lblSizesTopInfo.Location = New-Object System.Drawing.Point(420, 20)
$lblSizesTopInfo.Size = New-Object System.Drawing.Size(100, 23)
$panelSizesOptions.Controls.Add($lblSizesTopInfo)

# Include files option
$chkSizesIncludeFiles = New-Object System.Windows.Forms.CheckBox
$chkSizesIncludeFiles.Text = "Include files in root folder"
$chkSizesIncludeFiles.Location = New-Object System.Drawing.Point(250, 50)
$chkSizesIncludeFiles.Size = New-Object System.Drawing.Size(200, 23)
$chkSizesIncludeFiles.Checked = $false
$panelSizesOptions.Controls.Add($chkSizesIncludeFiles)

# Analyze button
$btnAnalyzeSizes = New-Object System.Windows.Forms.Button
$btnAnalyzeSizes.Text = "Analyze Folder Sizes"
$btnAnalyzeSizes.Location = New-Object System.Drawing.Point(20, 180)
$btnAnalyzeSizes.Size = New-Object System.Drawing.Size(150, 35)
$tabSizes.Controls.Add($btnAnalyzeSizes)

# Results textbox
$txtSizesResults = New-Object System.Windows.Forms.TextBox
$txtSizesResults.Location = New-Object System.Drawing.Point(20, 230)
$txtSizesResults.Size = New-Object System.Drawing.Size(730, 360)
$txtSizesResults.Multiline = $true
$txtSizesResults.ScrollBars = "Vertical"
$txtSizesResults.ReadOnly = $true
$txtSizesResults.Font = New-Object System.Drawing.Font("Consolas", 9)
$txtSizesResults.Anchor = [System.Windows.Forms.AnchorStyles]::Top -bor [System.Windows.Forms.AnchorStyles]::Bottom -bor [System.Windows.Forms.AnchorStyles]::Left -bor [System.Windows.Forms.AnchorStyles]::Right
$tabSizes.Controls.Add($txtSizesResults)

# Analyze folder sizes function
$btnAnalyzeSizes.Add_Click({
        $folderPath = $txtSizesFolder.Text
    
        if (-not $folderPath) {
            [System.Windows.Forms.MessageBox]::Show("Please select a folder to analyze.", "Missing Information", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
            return
        }
    
        if (-not (Test-Path -Path $folderPath)) {
            [System.Windows.Forms.MessageBox]::Show("Folder path does not exist.", "Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
            return
        }
    
        $txtSizesResults.Clear()
        $txtSizesResults.AppendText("Starting folder size analysis...`r`n")
        $txtSizesResults.AppendText("Folder: $folderPath`r`n`r`n")
    
        # Get options
        $depth = $numSizesDepth.Value
        $sortBySize = $chkSizesSortBySize.Checked
        $top = $numSizesTop.Value
        $includeFiles = $chkSizesIncludeFiles.Checked
    
        $statusLabel.Text = "Analyzing folder sizes..."
    
        # Create a PowerShell process to run the get_folder_sizes.ps1 script
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo.FileName = "powershell.exe"
        $process.StartInfo.Arguments = "-ExecutionPolicy Bypass -File `"$getFolderSizesPath`" -FolderPath `"$folderPath`" -Depth $depth -SortBySize `$$sortBySize -Top $top -IncludeFiles `$$includeFiles"
        $process.StartInfo.UseShellExecute = $false
        $process.StartInfo.RedirectStandardOutput = $true
        $process.StartInfo.RedirectStandardError = $true
        $process.StartInfo.CreateNoWindow = $true
    
        $outputBuilder = New-Object System.Text.StringBuilder
        $errorBuilder = New-Object System.Text.StringBuilder
    
        $outputHandler = [System.EventHandler[System.Diagnostics.DataReceivedEventArgs]] {
            if (-not [String]::IsNullOrEmpty($EventArgs.Data)) {
                $outputBuilder.AppendLine($EventArgs.Data)
                $txtSizesResults.AppendText($EventArgs.Data + "`r`n")
                $txtSizesResults.ScrollToCaret()
                [System.Windows.Forms.Application]::DoEvents()
            }
        }
    
        $errorHandler = [System.EventHandler[System.Diagnostics.DataReceivedEventArgs]] {
            if (-not [String]::IsNullOrEmpty($EventArgs.Data)) {
                $errorBuilder.AppendLine($EventArgs.Data)
                $txtSizesResults.AppendText("ERROR: " + $EventArgs.Data + "`r`n")
                $txtSizesResults.ScrollToCaret()
                [System.Windows.Forms.Application]::DoEvents()
            }
        }
    
        $process.OutputDataReceived += $outputHandler
        $process.ErrorDataReceived += $errorHandler
    
        $process.Start() | Out-Null
        $process.BeginOutputReadLine()
        $process.BeginErrorReadLine()
        $process.WaitForExit()
    
        $txtSizesResults.AppendText("`r`nFolder size analysis complete!`r`n")
        $statusLabel.Text = "Folder size analysis complete."
    })
#endregion

# Add export results buttons to each tab
$btnExportOrganizerResults = New-Object System.Windows.Forms.Button
$btnExportOrganizerResults.Text = "Export Results"
$btnExportOrganizerResults.Location = New-Object System.Drawing.Point(310, 140)
$btnExportOrganizerResults.Size = New-Object System.Drawing.Size(150, 35)
$tabOrganizer.Controls.Add($btnExportOrganizerResults)

$btnExportDuplicatesResults = New-Object System.Windows.Forms.Button
$btnExportDuplicatesResults.Text = "Export Results"
$btnExportDuplicatesResults.Location = New-Object System.Drawing.Point(180, 220)
$btnExportDuplicatesResults.Size = New-Object System.Drawing.Size(150, 35)
$tabDuplicates.Controls.Add($btnExportDuplicatesResults)

$btnExportSizesResults = New-Object System.Windows.Forms.Button
$btnExportSizesResults.Text = "Export Results"
$btnExportSizesResults.Location = New-Object System.Drawing.Point(180, 180)
$btnExportSizesResults.Size = New-Object System.Drawing.Size(150, 35)
$tabSizes.Controls.Add($btnExportSizesResults)

# Export results functions
function Export-Results {
    param (
        [System.Windows.Forms.TextBox]$TextBox,
        [string]$DefaultFileName
    )
    
    $saveFileDialog = New-Object System.Windows.Forms.SaveFileDialog
    $saveFileDialog.Filter = "Text files (*.txt)|*.txt|All files (*.*)|*.*"
    $saveFileDialog.DefaultExt = "txt"
    $saveFileDialog.FileName = $DefaultFileName
    
    if ($saveFileDialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $TextBox.Text | Out-File -FilePath $saveFileDialog.FileName -Encoding utf8
        [System.Windows.Forms.MessageBox]::Show("Results exported successfully to $($saveFileDialog.FileName)", "Export Complete", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
    }
}

$btnExportOrganizerResults.Add_Click({
        Export-Results -TextBox $txtOrganizerResults -DefaultFileName "FileOrganizer_Results.txt"
    })

$btnExportDuplicatesResults.Add_Click({
        Export-Results -TextBox $txtDuplicatesResults -DefaultFileName "DuplicateFinder_Results.txt"
    })

$btnExportSizesResults.Add_Click({
        Export-Results -TextBox $txtSizesResults -DefaultFileName "FolderSizes_Results.txt"
    })

# Add help buttons to each tab
function Show-Help {
    param (
        [string]$Title,
        [string]$Content
    )
    
    [System.Windows.Forms.MessageBox]::Show($Content, $Title, [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
}

$btnOrganizerHelp = New-Object System.Windows.Forms.Button
$btnOrganizerHelp.Text = "?"
$btnOrganizerHelp.Location = New-Object System.Drawing.Point(730, 30)
$btnOrganizerHelp.Size = New-Object System.Drawing.Size(25, 25)
$btnOrganizerHelp.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$tabOrganizer.Controls.Add($btnOrganizerHelp)

$btnDuplicatesHelp = New-Object System.Windows.Forms.Button
$btnDuplicatesHelp.Text = "?"
$btnDuplicatesHelp.Location = New-Object System.Drawing.Point(730, 20)
$btnDuplicatesHelp.Size = New-Object System.Drawing.Size(25, 25)
$btnDuplicatesHelp.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$tabDuplicates.Controls.Add($btnDuplicatesHelp)

$btnSizesHelp = New-Object System.Windows.Forms.Button
$btnSizesHelp.Text = "?"
$btnSizesHelp.Location = New-Object System.Drawing.Point(730, 30)
$btnSizesHelp.Size = New-Object System.Drawing.Size(25, 25)
$btnSizesHelp.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$tabSizes.Controls.Add($btnSizesHelp)

$btnOrganizerHelp.Add_Click({
        Show-Help -Title "File Organizer Help" -Content @"
File Organizer

This tool organizes files into folders based on their last modified year.

Instructions:
1. Select a source folder containing the files you want to organize.
2. Choose whether to use the same folder as destination or specify a different one.
3. Click 'Organize Files' to start the process.

The tool will:
- Create year folders (e.g., 2022, 2023) based on file modification dates
- Maintain the original folder structure within each year folder
- Move files to their respective year folders
"@
    })

$btnDuplicatesHelp.Add_Click({
        Show-Help -Title "Duplicate Finder Help" -Content @"
Duplicate Finder

This tool finds duplicate files across multiple folders using file hash comparison.

Instructions:
1. Add one or more folders to scan using the 'Add Folder' button.
2. Select a hash algorithm (SHA256 recommended for accuracy).
3. Optionally check 'Save results to file' to export the results.
4. Click 'Find Duplicates' to start the search.

The tool will:
- Scan all files in the selected folders
- Calculate hash values for each file
- Group files with identical hash values
- Display sets of duplicate files with their sizes and locations
"@
    })

$btnSizesHelp.Add_Click({
        Show-Help -Title "Folder Size Analyzer Help" -Content @"
Folder Size Analyzer

This tool analyzes folder sizes and displays them in a human-readable format.

Instructions:
1. Select a folder to analyze.
2. Set the scan depth (how many levels of subfolders to analyze).
3. Choose whether to sort by size and how many top results to show.
4. Optionally include files in the root folder.
5. Click 'Analyze Folder Sizes' to start the analysis.

The tool will:
- Calculate the size of each subfolder
- Display results sorted by size (if selected)
- Show human-readable sizes (KB, MB, GB, etc.)
"@
    })

# Show the form
$form.ShowDialog() | Out-Null
