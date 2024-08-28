import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import getpass
import ssl
import os
import json

# Ignore SSL warnings (only for testing purposes)
context = ssl._create_unverified_context()

SERVER_LIST_FILE = "servers.json"


class PasswordDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Enter Password")
        self.top.geometry("300x100")
        self.top.resizable(False, False)

        tk.Label(self.top, text="Password:").pack(pady=10)
        
        self.password_entry = tk.Entry(self.top, show="*")
        self.password_entry.pack(padx=10)
        self.password_entry.focus_set()

        self.button = tk.Button(self.top, text="OK", command=self.on_ok)
        self.button.pack(pady=10)

        self.password = None

        # Bind the Enter key to the OK button
        self.password_entry.bind("<Return>", lambda event: self.on_ok())

        # Wait for user input
        self.top.grab_set()
        parent.wait_window(self.top)

    def on_ok(self):
        self.password = self.password_entry.get()
        self.top.destroy()


class vSphereSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("vSphere File Search Tool")

        # Load Server List
        self.server_list = self.load_server_list()

        # Configure grid layout to make widgets resizable
        root.columnconfigure(1, weight=1)
        root.rowconfigure(5, weight=1)

        # Server Input / Selection
        self.label_server = tk.Label(root, text="vCenter Server:")
        self.label_server.grid(row=1, column=0, padx=10, pady=5, sticky="e")

        self.combobox_server = ttk.Combobox(root, state="readonly")
        self.combobox_server.grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        self.combobox_server["values"] = self.server_list

        if self.server_list:
            self.combobox_server.current(0)

        # Add and Remove buttons for server
        self.button_add_server = tk.Button(root, text="Add Server", command=self.add_server)
        self.button_add_server.grid(row=0, column=1, padx=5, pady=5)

        self.button_remove_server = tk.Button(root, text="Remove Server", command=self.remove_server)
        self.button_remove_server.grid(row=0, column=2, padx=5, pady=5)

        # Connect button
        self.button_connect = tk.Button(root, text="Connect", command=self.connect_to_vcenter)
        self.button_connect.grid(row=1, column=3, padx=10, pady=5)

        # Datacenter selection
        self.label_datacenter = tk.Label(root, text="Datacenter:")
        self.label_datacenter.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        
        self.combobox_datacenter = ttk.Combobox(root, state="readonly")
        self.combobox_datacenter.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        self.combobox_datacenter.bind("<<ComboboxSelected>>", lambda event: self.update_datastore_list())


        # Option to search datacenters
        self.search_all_datacenters_var = tk.IntVar()
        self.checkbox_all_datacenters = tk.Checkbutton(root, text="Search all datacenters", variable=self.search_all_datacenters_var, command=self.toggle_datacenter_selection)
        self.checkbox_all_datacenters.grid(row=2, column=3, padx=10, pady=5, sticky="w")

        # Datastore selection
        self.label_datastore = tk.Label(root, text="Datastore:")
        self.label_datastore.grid(row=3, column=0, padx=10, pady=5, sticky="e")

        self.combobox_datastore = ttk.Combobox(root, state="disabled")
        self.combobox_datastore.grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # Option to search specific datastore
        self.search_specific_datastore_var = tk.IntVar()
        self.checkbox_specific_datastore = tk.Checkbutton(root, text="Search specific datastore", variable=self.search_specific_datastore_var, command=self.toggle_datastore_selection)
        self.checkbox_specific_datastore.grid(row=3, column=3, padx=10, pady=5, sticky="w")

        # Search input
        self.label_search = tk.Label(root, text="Search for file:")
        self.label_search.grid(row=4, column=0, padx=10, pady=5, sticky="e")

        self.entry_search = tk.Entry(root, width=30)
        self.entry_search.grid(row=4, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        # Bind Enter
        self.entry_search.bind("<Return>", lambda event: self.search_files())

        # Search button
        self.button_search = tk.Button(root, text="Search", command=self.search_files)
        self.button_search.grid(row=4, column=3, padx=10, pady=5)
        
        # Results textbox
        self.text_results = tk.Text(root, height=10)
        self.text_results.grid(row=5, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")
        
        # Export button
        self.button_export = tk.Button(root, text="Export Results", command=self.export_results, state="disabled")
        self.button_export.grid(row=6, column=1, padx=10, pady=5)

        # Disconnect Button
        # self.button_disconnect = tk.Button(root, text="Disconnect", command=self.Disconnect(si))
        # self.button_disconnect.grid(row=6, column=3, padx=5, pady=5)

    def load_server_list(self):
        """load the list of server from a JSON file,"""
        if os.path.exists(SERVER_LIST_FILE):
            with open(SERVER_LIST_FILE, "r") as file:
                return json.load(file)
        return []

    def save_server_list(self):
        """Save the list of servers to a JSON file."""
        with open(SERVER_LIST_FILE, 'w') as file:
            json.dump(self.server_list, file)

    def add_server(self):
        new_server = simpledialog.askstring("Add Server", "Enter vCenter Server:")
        if new_server and new_server not in self.server_list:
            self.server_list.append(new_server)
            self.save_server_list()
            self.combobox_server["values"] = self.server_list
            self.combobox_server.set(new_server)

    def remove_server(self):
        current_server = self.combobox_server.get()
        if current_server in self.server_list:
            self.server_list.remove(current_server)
            self.save_server_list()
            self.combobox_server["values"] = self.server_list
            self.combobox_server.set("" if not self.server_list else self.server_list[0])

    def toggle_datacenter_selection(self):
        if self.search_all_datacenters_var.get():
            self.combobox_datacenter.config(state="disabled")
        else:
            self.combobox_datacenter.config(state="readonly")
        self.update_datastore_list()

    def toggle_datastore_selection(self):
        if self.search_specific_datastore_var.get():
            self.combobox_datastore.config(state="readonly")
            self.update_datastore_list()
        else:
            self.combobox_datastore.config(state="disabled")
            self.combobox_datastore.set("")

    def connect_to_vcenter(self):
        # Prompt for password using the PasswordDialog
        password_dialog = PasswordDialog(self.root)
        password = password_dialog.password

        # Prompt for username and password
        # username = os.getlogin()
        # password = getpass.getpass(f"Enter password for {username}: ")

        # Connect to vCenter server
        try:
            self.si = SmartConnect(
                host=self.combobox_server.get(),
                user=os.getlogin(),
                pwd=password,
                port=443,
                sslContext=context
            )
            self.content = self.si.RetrieveContent()
            self.list_datacenters()
            messagebox.showinfo("Connecter", "Successfully connected to vCenter Server")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to vCenter: {e}")

    def list_datacenters(self):
        datacenters = [dc.name for dc in self.content.rootFolder.childEntity if isinstance(dc, vim.Datacenter)]
        self.combobox_datacenter['values'] = datacenters
        if datacenters:
            self.combobox_datacenter.current(0)
        self.update_datastore_list()
    
    def update_datastore_list(self):
        if not self.search_all_datacenters_var.get():
            datacenter_name = self.combobox_datacenter.get()
            datastores = self.get_datastores_in_datacenter(datacenter_name)
            datastore_names = [ds.name for ds in datastores]
            self.combobox_datastore["values"] = datastore_names
            if datastore_names:
                self.combobox_datastore.current(0)
        else:
            self.combobox_datastore.set("")
            self.combobox_datastore.config(state="disabled")

    def search_files(self):
        datacenters_to_search = []
        if self.search_all_datacenters_var.get():
            datacenters_to_search = [dc.name for dc in self.content.rootFolder.childEntity if isinstance(dc, vim.Datacenter)]
        else:
            datacenters_to_search = [self.combobox_datacenter.get()]

        search_pattern = f"*{self.entry_search.get()}*"
        results = []

        self.text_results.delete(1.0, tk.END) # Clear prev results

        for datacenter_name in datacenters_to_search:
            datastores = self.get_datastores_in_datacenter(datacenter_name)

            if self.search_specific_datastore_var.get():
                datastores = [ds for ds in datastores if ds.name == self.combobox_datastore.get()]            

            for datastore in datastores:
                if ("storage1" in datastore.name):
                    self.text_results.insert(tk.END, f"Searching in datastore: {datastore.name}...\n")
                    self.text_results.see(tk.END) # Scroll to the end to show the latest update
                    self.root.update_idletasks() # Force the GUI to update

                    found_files = self.search_file_in_datastore(datastore, search_pattern)
                    if found_files:
                        for file in found_files:
                            results.append(f"Datastore: {datastore.name} - File: {file}")
                            self.text_results.insert(tk.END, f"Found: {file}\n")
                            self.text_results.see(tk.END)
                            self.root.update_idletasks()
                    else:
                        self.text_results.insert(tk.END, f"No matching files found in datastore {datastore.name}.\n")
                        self.text_results.see(tk.END)
                        self.root.update_idletasks()
                else:
                    continue

        if results:
            self.button_export.config(state="normal")
        else:
            self.button_export.config(state="disabled")

    def get_datastores_in_datacenter(self, datacenter_name):
        for dc in self.content.rootFolder.childEntity:
            if isinstance(dc, vim.Datacenter) and dc.name == datacenter_name:
                return dc.datastore
        return []
    
    def search_file_in_datastore(self, datastore, file_pattern):
        search_spec = vim.HostDatastoreBrowserSearchSpec()
        search_spec.matchPattern = [file_pattern]

        task = datastore.browser.SearchDatastoreSubFolders_Task(
            datastorePath=f"[{datastore.name}]",
            searchSpec=search_spec
        )

        while task.info.state == vim.TaskInfo.State.running:
            continue

        if task.info.state == vim.TaskInfo.State.success:
            results = task.info.result
            found_files = []
            for result in results:
                for file in result.file:
                    found_files.append(f"{result.folderPath}{file.path}")
            return found_files
        else:
            messagebox.showerror("Error", f"Search task failed on datastore {datastore.name}: {task.info.error}")
            return []
        
    def export_results(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "w") as file:
                file.write(self.text_results.get(1.0, tk.END))
            messagebox.showinfo("Exported", f"Results successfully exported to {file_path}")

def main():
    root = tk.Tk()
    app = vSphereSearchApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

