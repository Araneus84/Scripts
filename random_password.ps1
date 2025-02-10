function Generate-RandPass {
    param (
        [int]$Length = 3
    )

    # Define character sets
    $letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ".ToCharArray()
    $digits = "0123456789".ToCharArray()
    $symbols = "!@#$%^&*()-_=+".ToCharArray()

    # Ensure password contains at least one character from each set
    $password = @()
    $password += ($letters | Get-Random -Count 1)
    $password += ($digits | Get-Random -Count 1)
    $password += ($symbols | Get-Random -Count 1)

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

# Example usage
$password = Generate-RandPassPass
Write-Output $password