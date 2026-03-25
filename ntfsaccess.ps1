
# Import NTFSAccess module if not already loaded
Import-Module NTFSAccess

# Get all folders recursively
$folders = Get-ChildItem -Path "Z:\Tv" -Directory -Recurse

# # Enable inheritance on parent folder first
# Enable-NTFSAccessInheritance -Path "Z:\Tv"

# Get parent folder permissions to apply
$parentPermissions = Get-NTFSAccess -Path "Z:\Tv"

# Enable inheritance and apply permissions to all subfolders
foreach ($folder in $folders) {
    Enable-NTFSAccessInheritance -Path $folder.FullName
    
    # Remove existing permissions
    # Get-NTFSAccess -Path $folder.FullName | Remove-NTFSAccess
    
    # Apply parent folder permissions
    foreach ($permission in $parentPermissions) {
        Add-NTFSAccess -Path $folder.FullName `
            -Account $permission.Account `
            -AccessRights $permission.AccessRights `
            -AccessControlType $permission.AccessControlType
    }
}
# Get accounts with SIDs that can't be resolved
$sidAccounts = Get-NTFSAccess -Path "Z:\Tv" | Where-Object { $_.Account -match '^S-1-' }

# Remove each unresolved SID account
foreach ($sidAccount in $sidAccounts) {
    Remove-NTFSAccess -Path "Z:\Tv" -Account $sidAccount.Account
}
