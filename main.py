#!/usr/bin/env python3
"""MobaxterN — a simple SSH terminal and SFTP client."""

import sys
import tkinter as tk

from ui.main_window import MainWindow


def main() -> int:
    print("Starting MobaxterN...", flush=True)
    root = MainWindow()
    try:
        root.tk.call("tk", "scaling", 1.5)
    except tk.TclError:
        pass
    root.lift()
    root.attributes("-topmost", True)
    root.after(200, lambda: root.attributes("-topmost", False))
    root.focus_force()
    print("MobaxterN is running. The window should be open — this terminal stays busy until you close it.", flush=True)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
