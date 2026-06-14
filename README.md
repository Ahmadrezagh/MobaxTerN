# MobaxterN

A simple Mobaxterm-style desktop SSH client with an interactive command line and SFTP file browser.

## Features

- **Saved SSH sessions** — host, port, username, password, or private key
- **Command line** — real terminal over SSH (history, Ctrl+C, clear)
- **SFTP sidebar** — directory tree when connected, with upload/download
- **Dark mode** — toggle in sidebar or File menu
- **Cross-platform** — Windows, macOS, Linux

## Download (releases)

Pre-built binaries are published on [GitHub Releases](https://github.com/Ahmadrezagh/MobaxTerN/releases).

| Platform | File | Run |
|----------|------|-----|
| **Windows** | `MobaxterN-windows-x64.zip` | Extract, then run `MobaxterN\MobaxterN.exe` |
| **macOS** | `MobaxterN-macos-universal.zip` | Extract, then open `MobaxterN.app` |
| **Linux** | `MobaxterN-linux-x64.tar.gz` | Extract, then run `MobaxterN/MobaxterN` |

> macOS may block the first launch: right-click the app → **Open** → **Open**.

Sessions and settings are stored in `~/.mobaxtern/`.

## Run from source

### Requirements

- Python 3.10+
- Tkinter (included with most Python installs; on Linux: `sudo apt install python3-tk`)

### Install

```bash
git clone https://github.com/Ahmadrezagh/MobaxTerN.git
cd MobaxTerN
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Start

```bash
python main.py
```

## Usage

1. Click **New** and enter session details
2. Click **Connect** on a session (or double-click it)
3. **Left sidebar** — SFTP file browser
4. **Right panel** — SSH command line
5. Click **Disconnect** at the top of the SFTP sidebar to return to sessions

## Build a release locally

```bash
pip install -r requirements-build.txt
pyinstaller --noconfirm mobaxtern.spec
```

Output is in `dist/` (`.app` on macOS, folder on Windows/Linux).

## Publish a GitHub release

1. Update `VERSION` if needed
2. Commit and push to `main`
3. Create and push a tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions builds Windows, macOS, and Linux packages and attaches them to the release automatically.

## Notes

Passwords are stored locally in plain text at `~/.mobaxtern/sessions.json`. For production use, prefer SSH keys.
