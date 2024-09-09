

Get-Process | where {$_.name -like "*manic*"} | Stop-Process

winget uninstall manictime

