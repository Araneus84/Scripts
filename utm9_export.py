import requests
import urllib3

# Suppress SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from os import getenv


def create_session():
    session = requests.Session()
    # First authenticate to get a valid token
    auth_data = {
        "username": UTM9_USER,
        "password": UTM9_PASS
    }
    session.verify = False
    auth_response = session.post(f"{UTM9_URL}/login", json=auth_data)
    auth_response.raise_for_status()
    token = auth_response.json().get('token')
    
    session.headers.update({
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    })
    return session

session = create_session()
try:
    response = session.get(f"{UTM9_URL}/objects/backup/export")
    response.raise_for_status()
    with open("utm9_config.abf", "wb") as f:
        f.write(response.content)
except requests.exceptions.RequestException as e:
    print(f"Error during API request: {e}")

OUTPUT_PATH = getenv("OUTPUT_PATH", "utm9_config.abf")