import requests
from requests.auth import HTTPBasicAuth
from os import getenv
# UTM9 API credentials
UTM9_URL = getenv()
UTM9_USER = getenv()
UTM9_TOKEN = getenv()
UTM9_PASS = getenv()
OUTPUT_PATH = getenv()

session = requests.Session()
session.auth = HTTPBasicAuth(UTM9_USER, UTM9_PASS)
session.verify = False  # Disable SSL verification (use with caution)

response = session.get(f"{UTM9_URL}/objects/backup/export")
if response.status_code == 200:
    with open("utm_config.abf", "wb") as f:
        f.write(response.content)
    print("Configuration exported successfully")
else:
    print(f"Error exporting configuration: {response.status_code}")
