$cred = Import-Clixml -Path "C:\Users\alexk\Documents\creds.xml"
Connect-VIServer vcenter.vsphere.local -Credential $cred

$datastores = Get-Datastore -Location EU-LO

'''
foreach($store in $datastores){
    if ($store -match "storage1"){
        $storeName = $store.Name
        $path = "$($store.DatastoreBrowserPath)\trash"
        if (Test-Path $path){
            Get-ChildItem -Recurse $path | where {$_.Name -like "*mavic*"}
        }else{
            Write-Host "The $path is invalid"
        }
    }
}
'''

# DatastoreBrowserPath           : vmstores:\vcenter.vsphere.local@443\EU-ST\vm1702:storage1
