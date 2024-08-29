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

def list_datastores(content):
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True)
    datastore_list = container.view
    container.Destroy()

    for datastore in datastore_list:
        print(f"Datastore name: {datastore.name}")
        print(f"    capacity: {datastore.summary.capacity / (1024**3)} GB")
        print(f"    Free Space: {datastore.summary.freeSpace / (1024**3)} GB")
        print(f"    Type: {datastore.summary.type}")



# list_datastores(content)

# Remember to disconnect when done
# Disconnect(si)
