# MobaxterN

A simple Mobaxterm-style desktop client with SSH sessions, an interactive command line tab, and SFTP file transfer.

## Features

- **Saved SSH sessions** — store host, port, username, password, and private key
- **Command line tab** — interactive shell over SSH
- **SFTP tab** — remote directory tree with path bar at the top
- **Upload / download** — transfer files to and from the selected remote directory
- **GUI** — session list, tabs, toolbar, and menus

## Requirements

- Python 3.10+ (includes Tkinter for the GUI)
- macOS, Linux, or Windows

## Install

```bash
cd MobaxTerN
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt   # only paramiko
```

## Run

```bash
python main.py
```

## Usage

1. **File → New Session** — enter name, host, port, username, and password or key file
2. Select a session and click **Connect** (or double-click the session)
3. Use the **Command Line** tab for the remote shell
4. Use the **SFTP** tab to browse folders, see the current path at the top, and upload/download files

Sessions are saved to `~/.mobaxtern/sessions.json`.

## Notes

This is a sample application. Passwords are stored locally in plain text. For production use, prefer SSH keys and a secure credential store.
