import json
import os

SERVER_LIST_FILE = "servers.json"

class ConfigManager:
    def load_server_list(self):
        """Load the list of servers from a JSON file."""
        if os.path.exists(SERVER_LIST_FILE):
            with open(SERVER_LIST_FILE, 'r') as file:
                return json.load(file)
        return []

    def save_server_list(self, server_list):
        """Save the list of servers to a JSON file."""
        with open(SERVER_LIST_FILE, 'w') as file:
            json.dump(server_list, file)
