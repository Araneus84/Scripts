import requests
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Disable SSL warnings (use with caution in production)
# requests.packages.urllib3.disable_warnings()

# Proxmox API setup
PROXMOX_HOST = 'https://your_proxmox_host:8006'
PROXMOX_USER = 'your_username@pve'
PROXMOX_PASSWORD = 'your_password'
PROXMOX_NODE = 'your_node_name'

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID'
RANGE_NAME = 'A1:A21'  # Assuming server names are in column A, rows 1-21

def get_proxmox_ticket():
    response = requests.post(
        f'{PROXMOX_HOST}/api2/json/access/ticket',
        verify=False,
        data={
            'username': PROXMOX_USER,
            'password': PROXMOX_PASSWORD
        }
    )
    result = response.json()['data']
    return {
        'PVEAuthCookie': result['ticket'],
        'CSRFPreventionToken': result['CSRFPreventionToken']
    }

def get_server_names_from_sheets():
    creds = Credentials.from_authorized_user_file('path/to/your/credentials.json', SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    return [row[0] for row in result.get('values', [])]

def create_vm(name, ticket):
    vm_id = get_next_vmid(ticket)
    data = {
        'vmid': vm_id,
        'name': f'XG{name}',
        'ostype': 'l26',
        'memory': 2048,
        'cores': 2,
        'sockets': 1,
        'net0': 'virtio,bridge=vmbr0',
        'scsi0': 'storage1:32,format=qcow2'
    }
    
    response = requests.post(
        f'{PROXMOX_HOST}/api2/json/nodes/{PROXMOX_NODE}/qemu',
        verify=False,
        headers={
            'Cookie': f"PVEAuthCookie={ticket['PVEAuthCookie']}",
            'CSRFPreventionToken': ticket['CSRFPreventionToken']
        },
        data=data
    )
    
    if response.status_code == 200:
        print(f"Successfully created VM: XG{name}")
    else:
        print(f"Failed to create VM: XG{name}. Error: {response.text}")

def get_next_vmid(ticket):
    response = requests.get(
        f'{PROXMOX_HOST}/api2/json/cluster/nextid',
        verify=False,
        headers={'Cookie': f"PVEAuthCookie={ticket['PVEAuthCookie']}"}
    )
    return response.json()['data']

def main():
    server_names = get_server_names_from_sheets()
    ticket = get_proxmox_ticket()

    for name in server_names:
        create_vm(name, ticket)

if __name__ == "__main__":
    main()
