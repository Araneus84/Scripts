from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import getpass
import ssl

context = ssl._create_unverified_context()

# Connect to the vSphere server
si= SmartConnect(
    host="vcenter.vsphere.local",
    user="alexki",
    pwd=getpass.getpass("Input your password: "),
    port=443,
    sslContext=context
)

content = si.RetrieveContent()
# If successful, `si` is your ServiceInstance object
print("Connected to vSphere")

def list_datacenters(content):
    datacenters = content.rootFolder.childEntity
    for datacenter in datacenters:
        if isinstance(datacenter, vim.Datacenter):
            print(f"Datacenter name: {datacenter.name}")

# Example usage:
list_datacenters(content)

# Disconnect from vSphere
Disconnect(si)