from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import getpass
import ssl

# Ignore SSL warnings (only for testing purposes)
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

def get_datastores_in_datacenter(datacenter_name):
    # Find the datacenter by name
    datacenter = None
    for dc in content.rootFolder.childEntity:
        if isinstance(dc, vim.Datacenter) and dc.name == datacenter_name:
            datacenter = dc
            break

    if not datacenter:
        print(f"Datacenter {datacenter_name} not found.")
        return []
    return datacenter.datastore

def search_file_in_datastore(datastore, file_pattern):
    # Create a search spec for the file
    search_spec = vim.HostDatastoreBrowserSearchSpec()
    search_spec.matchPattern = [file_pattern]
    
    # Start the search task
    task = datastore.browser.SearchDatastoreSubFolders_Task(
        datastorePath=f"[{datastore.name}]",
        searchSpec=search_spec
    )

    # Wait for the task to complete
    while task.info.state == vim.TaskInfo.State.running:
        continue

    # Process the results
    if task.info.state == vim.TaskInfo.State.success:
        results = task.info.result
        found_files = []
        for result in results:
            for file in result.file:
                found_files.append(f"{result.folderPath}{file.path}")
        return found_files
    else:
        print(f"Search task failed on datastore {datastore.name}: {task.info.error}")
        return []

def search_file_across_datastores(datacenter_name, file_pattern):
    datastores = get_datastores_in_datacenter(datacenter_name)
    if not datastores:
        return

    for datastore in datastores:
        if ("storage1" in datastore.name):
            print(f"Searching in datastore: {datastore.name}")
            found_files = search_file_in_datastore(datastore, file_pattern)
            if found_files:
                print(f"Found files in datastore {datastore.name}:")
                for file in found_files:
                    print(f"  {file}")
            else:
                print(f"No matching files found in datastore {datastore.name}.")
        else:
            continue

def list_datacenters(content):
    datacenters = content.rootFolder.childEntity
    for datacenter in datacenters:
        if isinstance(datacenter, vim.Datacenter):
            print(f"Datacenter name: {datacenter.name}")

# def search_file_across_datacenter(datacenter, file_pattern):


# Example usage:
# Search for files that contain "log" in their name
search_file_across_datastores("EU-LO", "*testing*")

# Disconnect from vSphere
Disconnect(si)