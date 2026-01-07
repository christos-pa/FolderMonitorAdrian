# FolderMonitorAdrian 📁📨

FolderMonitorAdrian is a lightweight **Windows background utility** that monitors a folder in real time, **emails new files instantly**, and **automatically archives them** after detection.

Designed for operational environments where files must be acted on immediately with minimal user interaction.

---

## 🚀 Features

- 📂 Real-time folder monitoring
- ✉️ Instant email notifications on new files
- 🗂 Automatic file backup / archive after detection
- 🔄 Runs silently in the background
- 🔔 System tray icon support
- 🧰 Simple install & uninstall scripts
- ⚙️ Configuration via JSON file

---

## 📁 Included Files

Make sure all files remain in the **same folder**:

| File / Folder                    | Description                                                   |
| -------------------------------- | ------------------------------------------------------------- |
| `FolderMonitorAdrian.exe`        | Compiled Windows executable                                   |
| `FolderMonitorAdrian.py`         | Main Python application script                                |
| `FolderMonitorAdrian.spec`       | PyInstaller build specification                               |
| `config.json`                    | Configuration file (folders, email/SMTP settings)             |
| `foldermonitoradrian.ico`        | Application / tray icon                                       |
| `INSTALL.bat`                    | Installs and starts the folder monitor (run as Administrator) |
| `uninstall.bat`                  | Stops and removes the folder monitor                          |
| `FolderMonitorAdrian_ReadMe.pdf` | Detailed user guide and setup instructions                    |
| `README.md`                      | Project overview and usage instructions                       |



⚠️ Do **not** separate these files.

---

## ⚙️ Configuration (`config.json`)

The application is configured using `config.json`.

Typical settings include:
- Folder to monitor
- Backup/archive folder
- Email (SMTP) settings
- Recipient address

> ⚠️ **Do not commit real credentials to public repositories**.  
> Use placeholders or a `config.example.json` file when sharing.

---

## 🛠 Installation

1. Copy all files into a single folder
2. Right-click `INSTALL.bat`
3. Select **Run as Administrator**
4. The monitor will start automatically in the background

A tray icon will indicate the service is running.

---

## 🗑 Uninstall

1. Right-click `uninstall.bat`
2. Select **Run as Administrator**
3. The background monitor and scheduled tasks will be removed

---

## 🧠 Use Cases

- Automated document intake
- Operations & support teams
- File-based workflows
- Kiosk / parking / enterprise environments
- Any system requiring immediate file alerts

---

## 📄 Documentation

A full user guide is included:

📘 **FolderMonitorAdrian_ReadMe.pdf**

---

## 🧩 Tech Stack

- Python
- PyInstaller
- Windows Task Scheduler
- SMTP (email notifications)

---

## 📌 Version

**v1.0** – Initial stable release

---

## 👤 Author

Developed by **Christos Paraskevopoulos**  
GitHub: https://github.com/christos-pa


