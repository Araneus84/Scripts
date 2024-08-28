# Define an array of standard Windows services to filter out
$standardServices = @(
    'wuauserv',        # Windows Update
    'TrustedInstaller',# Windows Modules Installer
    'Spooler',         # Print Spooler
    'wscsvc',          # Security Center
    'WinDefend',       # Windows Defender
    'Schedule',        # Task Scheduler
    'eventlog',        # Windows Event Log
    'LanmanWorkstation',# Workstation
    'LanmanServer', 'WSLService', 'WSearch', 'wscsvc', 'Wpn*', 'W*'
)

# Get all services on the system
$services = Get-Service

# Filter out standard Windows services
$filteredServices = $services | Where-Object { $_.Name -notin $standardServices }

# Output the filtered list of services
$filteredServices | Format-Table -Property Name, DisplayName, Status

$filteredServices | Export-csv "Filtered_Services.csv" -NoTypeInformation

Get-Service | Where {$_.CanShutDown -like "TRUE" -and $_.CanStop -like "TRUE" -and $_.CanPauseAndContinue -like "TRUE"}