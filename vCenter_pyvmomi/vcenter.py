from pyVim.connect import SmartConnect, Disconnect
from tkinter import messagebox
import os
import ssl

# Ignore SSL warnings (only for testing purposes)
context = ssl._create_unverified_context()

class vCenterManager:
    def __init__(self, app):
        self.app = app
        self.si = None
        self.content = None

    def connect_to_vcenter(self):
        # Prompt for password using the PasswordDialog
        password_dialog = self.app.PasswordDialog(self.app.root)
        password = password_dialog.password

        # Connect to vCenter server
        try:
            self.si = SmartConnect(
                host=self.app.combobox_server.get(),
                user=os.getlogin(),  # Current logged-in username
                pwd=password,
                port=443,
                sslContext=context
            )
            self.content = self.si.RetrieveContent()
            self.app.list_datacenters()
            messagebox.showinfo("Connected", "Successfully connected to vCenter Server")
            self.app.button_disconnect.config(state="normal")  # Enable the disconnect button
            self.app.button_connect.config(state="disabled")  # Disable the connect button
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to vCenter: {e}")

    def disconnect_from_vcenter(self):
        if self.si:
            try:
                Disconnect(self.si)
                self.si = None
                self.app.button_disconnect.config(state="disabled")  # Disable the disconnect button
                self.app.button_connect.config(state="normal")  # Enable the connect button
                self.app.combobox_datacenter.set("")  # Clear datacenter selection
                self.app.combobox_datastore.set("")  # Clear datastore selection
                self.app.combobox_datacenter['values'] = []
                self.app.combobox_datastore['values'] = []
                messagebox.showinfo("Disconnected", "Successfully disconnected from vCenter Server")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to disconnect from vCenter: {e}")

    def get_datastores_in_datacenter(self, datacenter_name):
        for dc in self.content.rootFolder.childEntity:
            if isinstance(dc, vim.Datacenter) and dc.name == datacenter_name:
                return dc.datastore
        return []

    def search_files(self):
        datacenters_to_search = []
        if self.app.search_all_datacenters_var.get():
            datacenters_to_search = [dc.name for dc in self.content.rootFolder.childEntity if isinstance(dc, vim.Datacenter)]
        else:
            datacenters_to_search = [self.app.combobox_datacenter.get()]

        search_pattern = f"*{self.app.entry_search.get()}*"
        results = []

        self.app.text_results.delete(1.0, "end")  # Clear previous results

        for datacenter_name in datacenters_to_search:
            datastores = self.get_datastores_in_datacenter(datacenter_name)

            if self.app.search_specific_datastore_var.get():
                datastores = [ds for ds in datastores if ds.name == self.app.combobox_datastore.get()]

            for datastore in datastores:
                # Update the text widget with the current search status
                self.app.text_results.insert("end", f"Searching in datastore: {datastore.name} (Datacenter: {datacenter_name})...\n")
                self.app.text_results.see("end")  # Scroll to the end to show the latest update
                self.app.root.update_idletasks()  # Force the GUI to update

                found_files = self.search_file_in_datastore(datastore, search_pattern)
                if found_files:
                    for file in found_files:
                        results.append(f"Datacenter: {datacenter_name} - Datastore: {datastore.name} - File: {file}")
                        self.app.text_results.insert("end", f"Found: {file}\n")
                        self.app.text_results.see("end")  # Scroll to the end to show the latest update
                        self.app.root.update_idletasks()  # Force the GUI to update
                else:
                    self.app.text_results.insert("end", f"No matching files found in datastore {datastore.name}.\n")
                    self.app.text_results.see("end")  # Scroll to the end to show the latest update
                    self.app.root.update_idletasks()  # Force the GUI to update

        if results:
            self.app.button_export.config(state="normal")
        else:
            self.app.button_export.config(state="disabled")

    def search_file_in_datastore(self, datastore, file_pattern):
        search_spec = vim.HostDatastoreBrowserSearchSpec()
        search_spec.matchPattern = [file_pattern]
        
        task = datastore.browser.SearchDatastoreSubFolders_Task(
            datastorePath=f"[{datastore.name}]",
            searchSpec=search_spec
        )
        
        while task.info.state == vim.TaskInfo.State.running:
            continue
