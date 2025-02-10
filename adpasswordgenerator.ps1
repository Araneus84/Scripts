# Import Active Directory Module
Import-Module ActiveDirectory

# Define parameters for the password generator
function New-ADUserPassword {
    param (
        [int]$Length = 1
    )

    # Define character sets
    $letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ".ToCharArray()
    $digits = "0123456789".ToCharArray()
    $symbols = "!@#$%^&*".ToCharArray()

    # Ensure password contains at least one character from each set
    $password = @(
        ($letters | Get-Random -Count 1) +
        ($digits | Get-Random -Count 1) +
        ($symbols | Get-Random -Count 1)
    )

    # Calculate the remaining length
    $remainingLength = $Length - 3

    # Fill the rest of the password with random characters from all sets
    $allCharacters = $letters + $digits + $symbols
    if ($remainingLength -gt 0) {
        $password += ($allCharacters | Get-Random -Count $remainingLength)
    }

    # Shuffle the password to randomize the order
    return (-join ($password | Get-Random -Count $password.Length))
}

# Define output CSV file
$outputCsv = "C:\ADUserPasswords.csv"

# Initialize results array
$results = @()

# Get all Active Directory users
$users = Get-ADUser -Filter * -Properties SamAccountName | Where-Object { $_.Enabled -eq $true }

# Loop through users
foreach ($user in $users) {
    # Check if user is not in privileged groups
    $isAdmin = Get-ADPrincipalGroupMembership $user.SamAccountName | Where-Object {
        $_.Name -eq "Domain Admins" -or $_.Name -eq "Administrators"
    }

    if (-not $isAdmin) {
        # Generate a new password
        $newPassword = New-ADUserPassword

        try {
            # Set the new password for the user
            Set-ADAccountPassword -Identity $user.SamAccountName -Reset -NewPassword (ConvertTo-SecureString -AsPlainText $newPassword -Force)
            Unlock-ADAccount -Identity $user.SamAccountName

            # Log the user and their new password
            $results += [PSCustomObject]@{
                Username = $user.SamAccountName
                Password = $newPassword
            }
            Write-Host "Password changed for user: $($user.SamAccountName)" -ForegroundColor Green
        }
        catch {
            Write-Host "Failed to update password for user: $($user.SamAccountName). Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "Skipping admin user: $($user.SamAccountName)" -ForegroundColor Yellow
    }
}
# Export results to CSV
$results | Export-Csv -Path $outputCsv -NoTypeInformation -Encoding UTF8

Write-Host "Password changes completed. Results exported to $outputCsv" -ForegroundColor Yellow
