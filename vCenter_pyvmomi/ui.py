import tkinter as tk
from tkinter import ttk, messagebox
from vcenter import vCenterManager
from dialogs import PasswordDialog
from config import ConfigManager

class vSphereSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("vSphere File Search Tool")
        
        self.config_manager = ConfigManager()
        self.vcenter_manager = vCenterManager(self)

        # Load server list
        self.server_list = self.config_manager.load_server_list()
        
        # Configure grid layout to make widgets resizable
        root.columnconfigure(1, weight=1)
        root.rowconfigure(5, weight=1)
        
        # Server selection
        self.label_server = tk.Label(root, text="vCenter Server:")
        self.label_server.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        
        self.combobox_server = ttk.Combobox(root, state="readonly")
        self.combobox_server.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.combobox_server['values'] = self.server_list
        
        if self.server_list:
            self.combobox_server.current(0)
        
        # Add and Remove buttons for servers
        self.button_add_server = tk.Button(root, text="Add Server", command=self.add_server)
        self.button_add_server.grid(row=0, column=2, padx=5, pady=5)

        self.button_remove_server = tk.Button(root, text="Remove Server", command=self.remove_server)
        self.button_remove_server.grid(row=0, column=3, padx=5, pady=5)

        # Connect button
        self.button_connect = tk.Button(root, text="Connect", command=self.vcenter_manager.connect_to_vcenter)
        self.button_connect.grid(row=1, column=2, padx=10, pady=5)

        # Disconnect button
        self.button_disconnect = tk.Button(root, text="Disconnect", command=self.vcenter_manager.disconnect_from_vcenter, state="disabled")
        self.button_disconnect.grid(row=1, column=3, padx=10, pady=5)
        
        # Datacenter selection
        self.label_datacenter = tk.Label(root, text="Datacenter:")
        self.label_datacenter.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        
        self.combobox_datacenter = ttk.Combobox(root, state="readonly")
        self.combobox_datacenter.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.combobox_datacenter.bind("<<ComboboxSelected>>", lambda event: self.update_datastore_list())

        # Option to search all datacenters
        self.search_all_datacenters_var = tk.IntVar()
        self.checkbox_all_datacenters = tk.Checkbutton(root, text="Search all datacenters", variable=self.search_all_datacenters_var, command=self.toggle_datacenter_selection)
        self.checkbox_all_datacenters.grid(row=2, column=2, padx=10, pady=5, sticky="w")
        
        # Datastore selection
        self.label_datastore = tk.Label(root, text="Datastore:")
        self.label_datastore.grid(row=3, column=0, padx=10, pady=5, sticky="e")
        
        self.combobox_datastore = ttk.Combobox(root, state="disabled")  # Disabled by default
        self.combobox_datastore.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        # Option to search specific datastore
        self.search_specific_datastore_var = tk.IntVar()
        self.checkbox_specific_datastore = tk.Checkbutton(root, text="Search specific datastore", variable=self.search_specific_datastore_var, command=self.toggle_datastore_selection)
        self.checkbox_specific_datastore.grid(row=3, column=2, padx=10, pady=5, sticky="w")
        
        # Search input
        self.label_search = tk.Label(root, text="Search for file:")
        self.label_search.grid(row=4, column=0, padx=10, pady=5, sticky="e")
        
        self.entry_search = tk.Entry(root)
        self.entry_search.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        
        # Search button
        self.button_search = tk.Button(root, text="Search", command=self.search_files)
        self.button_search.grid(row=4, column=2, padx=10, pady=5)
        
        # Results textbox
        self.text_results = tk.Text(root, height=10)
        self.text_results.grid(row=5, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")
        
        # Export button
        self.button_export = tk.Button(root, text="Export Results", command=self.export_results, state="disabled")
        self.button_export.grid(row=6, column=1, padx=10, pady=5)

    def add_server(self):
        """Prompt the user to add a new server to the list."""
        new_server = tk.simpledialog.askstring("Add Server", "Enter vCenter Server:")
        if new_server and new_server not in self.server_list:
            self.server_list.append(new_server)
            self.config_manager.save_server_list(self.server_list)
            self.combobox_server['values'] = self.server_list
            self.combobox_server.set(new_server)

    def remove_server(self):
        """Remove the currently selected server from the list."""
        current_server = self.combobox_server.get()
        if current_server in self.server_list:
            self.server_list.remove(current_server)
            self.config_manager.save_server_list(self.server_list)
            self.combobox_server['values'] = self.server_list
            self.combobox_server.set('' if not self.server_list else self.server_list[0])

    def toggle_datacenter_selection(self):
        if self.search_all_datacenters_var.get():
            self.combobox_datacenter.config(state="disabled")
        else:
            self.combobox_datacenter.config(state="readonly")
        self.update_datastore_list()

    def toggle_datastore_selection(self):
        if self.search_specific_datastore_var.get():
            self.combobox_datastore.config(state="readonly")
            self.update_datastore_list()  # Ensure datastores are loaded when checkbox is checked
        else:
            self.combobox_datastore.config(state="disabled")
            self.combobox_datastore.set("")  # Clear the selection if disabled

    def update_datastore_list(self):
        """Refresh the datastore list based on the selected datacenter."""
        if not self.search_all_datacenters_var.get():
            datacenter_name = self.combobox_datacenter.get()
            datastores = self.vcenter_manager.get_datastores_in_datacenter(datacenter_name)
            datastore_names = [ds.name for ds in datastores]
            self.combobox_datastore['values'] = datastore_names
            if datastore_names:
                self.combobox_datastore.current(0)
        else:
            self.combobox_datastore.set("")
            self.combobox_datastore.config(state="disabled")

    def search_files(self):
        self.vcenter_manager.search_files()

    def export_results(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.text_results.get(1.0, tk.END))
            messagebox.showinfo("Exported", f"Results successfully exported to {file_path}")
