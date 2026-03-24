# Scripts

A personal collection of infrastructure automation, systems administration, and utility tools built across VMware, Proxmox, Active Directory, and general IT workflows.

---

## Table of Contents

- [vCenter Search Tool](#vcenter-search-tool)
- [Proxmox VM Provisioner (xg_deploy)](#proxmox-vm-provisioner-xg_deploy)
- [SSL Certificate Expiry Checker](#ssl-certificate-expiry-checker)
- [Keyboard Typing Simulator (BetterCopy)](#keyboard-typing-simulator-bettercopy)
- [Active Directory PowerShell Toolkit](#active-directory-powershell-toolkit)
- [File Management Suite (PowerShell)](#file-management-suite-powershell)
- [Password Generator Utilities](#password-generator-utilities)
- [UTM9 Config Exporter](#utm9-config-exporter)
- [Other Utilities](#other-utilities)

---

## vCenter Search Tool

**Files:** `vCenter_Search_fullApp.py` | `vCenter_pyvmomi/` (modular version)

### What it does

A full GUI application for searching files across VMware vSphere datastores. Connects to one or more vCenter servers, enumerates datacenters and datastores, and lets you search for files by name across your entire virtual infrastructure — without needing direct datastore browser access.

The `vCenter_pyvmomi/` directory contains a refactored, modular version of the same application, split across separate concerns: `ui.py` (Tkinter interface), `vcenter.py` (pyVmomi connection logic), `config.py` (server list persistence), and `dialogs.py` (reusable dialog components).

### Problem it solves

Finding a specific VM disk, ISO, or config file buried across dozens of datastores in a large vSphere environment is slow and error-prone through the vSphere Web Client. This tool lets you connect to any vCenter, select a datacenter and datastore (or search all at once), and get results in seconds via a native desktop UI.

### Tech stack

- Python 3
- `tkinter` / `ttk` — cross-platform GUI
- `pyVmomi` — official VMware Python SDK for vSphere API
- `ssl` — certificate context for vCenter connections
- JSON file persistence for saved server list

### Usage

```bash
pip install pyVmomi
python vCenter_Search_fullApp.py
```

1. Add your vCenter server hostname via "Add Server"
2. Click "Connect" and enter your vSphere credentials
3. Select a Datacenter and Datastore (or check "Search all datacenters")
4. Enter a filename pattern and click Search

---

## Proxmox VM Provisioner (xg_deploy)

**File:** `xg_deploy.py`

### What it does

Automates bulk VM creation on a Proxmox VE cluster by reading a list of server names from a Google Sheet and provisioning a VM for each entry via the Proxmox REST API. Each VM is created with a standardized configuration (CPU, RAM, disk, network bridge) and named with a consistent prefix (`XG<name>`).

### Problem it solves

Manually creating dozens of VMs through the Proxmox UI when deploying a new environment (e.g., firewall appliances, test nodes) is time-consuming and error-prone. This script reads a source-of-truth spreadsheet and provisions the full VM list in one run, ensuring consistent configuration across all instances.

### Tech stack

- Python 3
- `requests` — Proxmox VE REST API (`/api2/json`)
- `google-api-python-client` — Google Sheets API v4
- `google-auth` — OAuth2 credentials for Sheets access
- Proxmox ticket-based authentication (cookie + CSRF token)

### Usage

```bash
pip install requests google-api-python-client google-auth-oauthlib
# Edit PROXMOX_HOST, PROXMOX_USER, PROXMOX_PASSWORD, PROXMOX_NODE, SPREADSHEET_ID in script
python xg_deploy.py
```

The script authenticates to Proxmox, fetches the next available VMID, reads server names from the configured Google Sheet range, and creates a VM for each row.

---

## SSL Certificate Expiry Checker

**File:** `cert_exp.py`

### What it does

Connects to a list of domains over TLS (port 443) and reports the expiry date of each domain's SSL certificate. Domains are loaded from a `domains.json` file so the list can be maintained separately from the script.

### Problem it solves

Tracking certificate expiry dates manually across multiple external services and internal applications is easy to forget, often resulting in unexpected outages. This script provides a quick local audit of all monitored domains without relying on a third-party service.

### Tech stack

- Python 3 (standard library only — no pip dependencies)
- `ssl` — native TLS connection and certificate inspection
- `socket` — TCP connection to port 443
- `json` — domain list file

### Usage

```bash
# Create domains.json:
# ["example.com", "yourdomain.org", "internal.service.io"]

python cert_exp.py
```

**Example output:**
```
Domain: example.com, SSL Certificate Expiration Date: 2025-09-14 12:00:00
Domain: expired.example.com, Error: [SSL: CERTIFICATE_VERIFY_FAILED] ...
```

---

## Keyboard Typing Simulator (BetterCopy)

**Files:** `bettercopy.py` (Tkinter), `bettercopyqt6.py` (PyQt6)

### What it does

A desktop GUI tool that simulates keyboard input — typing text into any focused application exactly as if the user were pressing keys. Supports a configurable startup delay, clipboard paste, special characters (via shift-key mapping), and a hotkey-based stop mechanism.

The Qt6 version (`bettercopyqt6.py`) adds a clipboard history panel (up to 10 entries), current keyboard layout detection, and a more polished two-panel layout. Both versions handle special characters that `pyautogui` cannot type directly by translating them to the correct shift-key combinations.

### Problem it solves

Certain environments (KVM consoles, legacy web forms, RDP sessions with clipboard restrictions, IPMI interfaces) do not support paste operations. This tool lets you pre-load text, set a delay, switch focus to the target window, and have the text typed in character-by-character automatically.

### Tech stack

- Python 3
- `tkinter` / `PyQt6` — GUI framework (two independent implementations)
- `pyautogui` — cross-platform keyboard simulation
- `keyboard` — global hotkey listener (start/stop)
- `pyperclip` — clipboard access (Tkinter version)

### Usage

**Tkinter version:**
```bash
pip install pyautogui keyboard pyperclip
# Linux: run as root (required for /dev/input access)
sudo python bettercopy.py
```

**Qt6 version:**
```bash
pip install PyQt6 pyautogui keyboard
python bettercopyqt6.py
```

Set your text, configure the delay (default: 3 seconds), click Start, then switch to the target application. Use the configured hotkey (Shift+F10) to stop mid-typing if needed.

---

## Active Directory PowerShell Toolkit

**Files:** `adpasswordgenerator.ps1`, `random_password.ps1`

### adpasswordgenerator.ps1

Generates a compliant random password for every enabled Active Directory user (excluding Domain Admins and Administrators group members), resets each account password via `Set-ADAccountPassword`, forces a password change at next login, and exports results to a CSV at `C:\ADUserPasswords.csv`.

**Tech stack:** PowerShell 5+, `ActiveDirectory` module (RSAT)

**Use case:** Bulk credential rotation during security incidents, new environment provisioning, or compliance-driven password resets without manually touching each account.

```powershell
# Run from a domain-joined machine with RSAT installed
.\adpasswordgenerator.ps1
```

### random_password.ps1

A standalone password generation function (`Generate-RandPass`) that produces cryptographically shuffled passwords containing at least one letter, one digit, and one symbol. Configurable length parameter. Designed as a utility function to be dot-sourced or called from other scripts.

```powershell
. .\random_password.ps1
$pwd = Generate-RandPass -Length 16
```

---

## File Management Suite (PowerShell)

**Files:** `FileManagementTool.ps1`, `file_organizer.ps1`, `find_duplicates.ps1`, `find_duplicates.py`, `get_folder_sizes.ps1`

### FileManagementTool.ps1

A Windows Forms tabbed GUI application that combines three file management utilities into a single launcher. Tabs: File Organizer, Duplicate Finder, and Folder Size Analyzer. Validates that all three sub-scripts are present before launching.

**Tech stack:** PowerShell 5+, `System.Windows.Forms`, `System.Drawing`

### file_organizer.ps1

Recursively scans a source folder and reorganizes files into year-based subfolders using each file's `LastWriteTime`. Accepts a separate destination path, creating it if needed. Useful for archiving unsorted media, downloads, or log directories.

```powershell
.\file_organizer.ps1 -SourcePath "D:\Downloads" -DestinationPath "D:\Sorted"
```

### find_duplicates.ps1

Scans one or more folder paths, computes a cryptographic hash (SHA256 by default, configurable) for every file, groups results by hash to identify duplicates, and optionally exports the report to a file. Supports MD5, SHA1, SHA256, SHA384, SHA512.

```powershell
.\find_duplicates.ps1 -FolderPath "D:\Photos","E:\Backup" -Algorithm SHA256 -OutputFile duplicates.txt
```

### find_duplicates.py

A full PyQt6 GUI reimplementation of the duplicate finder with background worker threads (no UI freeze), a tree-view results panel, per-duplicate-group comparison, progress bar with ETA, and options to move/zip/delete duplicates. The GUI version is the primary tool for interactive use; the PS1 version is for scripted/scheduled runs.

**Tech stack:** Python 3, PyQt6, `hashlib`, `QThread`/`pyqtSignal` for non-blocking hashing

### get_folder_sizes.ps1

Recursively calculates the total size of each subdirectory up to a configurable depth, formats output in human-readable units (KB/MB/GB/TB), and optionally sorts by size descending. Useful for quickly identifying which folders are consuming the most disk space.

```powershell
.\get_folder_sizes.ps1 -FolderPath "D:\" -Depth 2 -Top 10 -SortBySize $true
```

---

## Password Generator Utilities

**Files:** `pass_gen.py`, `passwords.py`

### pass_gen.py

A minimal Tkinter GUI password generator. Supports configurable length (3–15 characters) and three character-set modes: Alphanumeric, Numeric, and Alpha-only. Generates random passwords using Python's `random` module and displays the result in the window.

**Tech stack:** Python 3, `tkinter`, `string`, `random`

### passwords.py

Complementary password utility (supporting module or standalone script).

---

## UTM9 Config Exporter

**Files:** `utm9_export.py`, `utm9_export copy.py`

### What it does

Authenticates to a Sophos UTM 9 appliance via its REST API using bearer-token auth, then downloads a full configuration backup (`.abf` format) to a local file. The output path is configurable via the `OUTPUT_PATH` environment variable.

### Problem it solves

Automating scheduled configuration backups from UTM9 appliances without needing manual UI access or SSH. Can be integrated into a cron job or CI pipeline to ensure offsite backup copies are always current.

### Tech stack

- Python 3
- `requests` — REST API client with session management
- `urllib3` — SSL warning suppression for self-signed certs
- Environment variables for credentials (`UTM9_USER`, `UTM9_PASS`, `UTM9_URL`)

```bash
export UTM9_URL="https://192.168.1.1:4444/api"
export UTM9_USER="admin"
export UTM9_PASS="yourpassword"
export OUTPUT_PATH="utm9_backup.abf"
python utm9_export.py
```

---

## Other Utilities

| File | Description |
|---|---|
| `backup_downloader.sh` | Shell script for downloading backups from a remote source |
| `launch.sh` / `run.sh` | Entry-point launcher scripts for application startup |
| `zip_split.sh` | Shell utility for splitting and zipping large files |
| `py_clusters.py` | Python clustering/grouping utility |
| `path.py` | Path manipulation helper |
| `markdown.py` | Markdown processing utility |
| `exercism.py` | Exercism platform helper/automation |
| `tkinter_aaa.py` | Tkinter UI component prototype |
| `testing.py` | Development test harness |
| `main.py` | Generic entry-point script |

---

## Repository Structure

```
Scripts/
├── vCenter_Search_fullApp.py   # vSphere file search GUI (single-file)
├── vCenter_pyvmomi/            # Modular refactor of vSphere search tool
│   ├── main.py
│   ├── ui.py
│   ├── vcenter.py
│   ├── config.py
│   └── dialogs.py
├── xg_deploy.py                # Proxmox bulk VM provisioner via Sheets
├── cert_exp.py                 # SSL certificate expiry checker
├── bettercopy.py               # Keyboard simulator (Tkinter)
├── bettercopyqt6.py            # Keyboard simulator (PyQt6, with history)
├── adpasswordgenerator.ps1     # AD bulk password reset + export
├── random_password.ps1         # Standalone password generation function
├── FileManagementTool.ps1      # Windows Forms tabbed file management GUI
├── file_organizer.ps1          # Year-based file sorter
├── find_duplicates.ps1         # Hash-based duplicate file finder (CLI)
├── find_duplicates.py          # Duplicate finder GUI (PyQt6)
├── get_folder_sizes.ps1        # Folder size analyzer
├── pass_gen.py                 # Password generator GUI (Tkinter)
├── utm9_export.py              # Sophos UTM9 config backup via REST API
└── ...
```

---

## Requirements

### Python tools

```bash
pip install pyVmomi pyautogui keyboard pyperclip PyQt6 google-api-python-client google-auth requests urllib3
```

### PowerShell tools

- PowerShell 5.1+ or PowerShell 7+
- RSAT (Remote Server Administration Tools) for AD cmdlets
- `ActiveDirectory` PowerShell module

### Credentials / configuration

- vCenter tools: vSphere credentials with datastore browse permissions
- `xg_deploy.py`: Proxmox API credentials + Google Cloud OAuth2 service account with Sheets read access
- `cert_exp.py`: `domains.json` file in the working directory
- `utm9_export.py`: `UTM9_URL`, `UTM9_USER`, `UTM9_PASS` environment variables
