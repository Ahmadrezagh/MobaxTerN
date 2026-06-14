# PyInstaller spec for MobaxterN (cross-platform GUI build).

import sys
from pathlib import Path

block_cipher = None
project_dir = Path(SPEC).resolve().parent

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "paramiko",
        "cryptography",
        "bcrypt",
        "nacl",
        "invoke",
        "core",
        "core.session_store",
        "core.settings_store",
        "core.ssh_client",
        "ui",
        "ui.main_window",
        "ui.session_dialog",
        "ui.sftp_panel",
        "ui.terminal_widget",
        "ui.theme",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MobaxterN",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MobaxterN",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="MobaxterN.app",
        icon=None,
        bundle_identifier="com.mobaxtern.app",
    )
