# PortMan_ML

**PortMan_ML** is a Python-based automation tool designed for managing and backing up various network devices including DSLAMs, OLTs, Mikrotik routers, and radio equipment. It integrates with Django for data access and supports cloud notifications and user management.

---

## 🚀 Features

- Automated backups for:
  - Fiberhome DSLAMs
  - Other DSLAM types
  - OLTs
  - Mikrotik Radios
- Cloud notifications and reminder system
- Django-based user group management
- Integration with Zabbix for monitoring support
- External API integration for FAT data

---

## 📁 Project Structure

- `bulk_commands/` – Core operation scripts
- `services/` – Logic and service utilities
- `requirements.txt` – Python dependencies
- `.idea/` – IDE project files
- `.gitignore` – Files and folders to exclude from Git

---

## 🧪 Installation

```bash
# Clone or extract the project
cd PortMan_ML-master

# Optional: set up virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 🔧 Module Descriptions & Usage

| Module | Description | Run Command |
|--------|-------------|-------------|
| `bulk_commands.py` | Imports backup utilities like VLAN, Mikrotik, Cisco, etc. | *Usually used as a module, not directly executed* |
| `cloud_notification.py` | Retrieves expiring config requests for notifications. | `python bulk_commands/cloud_notification.py` *(add main if needed)* |
| `dj_bridge.py` | Handles Django integration using dynamic paths. | *Imported by other scripts* |
| `fiberhome_dslam_backup.py` | Backups for Fiberhome DSLAM devices. | `python bulk_commands/fiberhome_dslam_backup.py` |
| `manage_user_groups.py` | Updates Django user groups based on user types. | `python bulk_commands/manage_user_groups.py` |
| `olt_backup.py` | Manages backup and timestamping for OLT devices. | `python bulk_commands/olt_backup.py` |
| `other_dslam_backup.py` | DSLAM backup for non-Fiberhome devices. | `python bulk_commands/other_dslam_backup.py` |
| `radio_backup.py` | Runs Mikrotik radio backups. | `python bulk_commands/radio_backup.py` |
| `reminder_sender.py` | Processes incomplete reminders. | `python bulk_commands/reminder_sender.py` |
| `save_to_partak.py` | Pushes FAT data to external API (PTE). | `python bulk_commands/save_to_partak.py` |
| `send_email.py` | Sends email alerts or messages via SMTP. | `python bulk_commands/send_email.py` |
| `utility.py` | Runs ICMP tests via JSON-RPC interface. | *Used internally* |
| `zabbix_hosts.py` | Updates Zabbix monitoring hosts and groups. | `python bulk_commands/zabbix_hosts.py` |

---

## 📊 Sample DSLAM Port Data

Below is a preview of the DSLAM port data used by the system for diagnostics and backup logic:

## Port Status Overview

| **id**   | **port_index** | **port_name** | **admin_status** | **oper_status** | **upstream_snr** | **downstream_snr** |
|---------:|---------------:|---------------|------------------|-----------------|------------------|--------------------|
| 562991   | 124            | adsl1-24      | UNLOCK           | SYNC            | 220.0            | 122.0              |
| 234316   | 259            | adsl2-59      | UNLOCK           | NO-SYNC         | 0.0              | 0.0                |
| 203030   | 736            | adsl7-36      | UNLOCK           | NO-SYNC         | 0.0              | 0.0                |
| 532635   | 225            | adsl2-25      | UNLOCK           | NO-SYNC         | *(missing)*      | *(missing)*        |
| 532633   | 229            | adsl2-29      | UNLOCK           | SYNC            | 7.5              | 6.2                |


These records include key operational metrics such as SNR levels, attenuation, admin/operational status, and more, which are vital for DSLAM diagnostics.

---

## 🛡 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Please create an issue or pull request as needed.
