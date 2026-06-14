"""Dialog to create or edit saved SSH sessions."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk

from core.session_store import SshSession
from ui.theme import COLORS


class SessionDialog(tk.Toplevel):
    def __init__(self, parent, session: SshSession | None = None) -> None:
        super().__init__(parent)
        self.title("Edit SSH Session" if session else "New SSH Session")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        self.result: SshSession | None = None

        self.name_var = tk.StringVar(value=session.name if session else "")
        self.host_var = tk.StringVar(value=session.host if session else "")
        self.port_var = tk.StringVar(value=str(session.port if session else 22))
        self.user_var = tk.StringVar(value=session.username if session else "")
        self.pass_var = tk.StringVar(value=session.password if session else "")
        self.key_var = tk.StringVar(value=session.key_file if session else "")

        frame = ttk.Frame(self, padding=16, style="Surface.TFrame")
        frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        fields = [
            ("Session name:", self.name_var),
            ("Host:", self.host_var),
            ("Port:", self.port_var),
            ("Username:", self.user_var),
            ("Password:", self.pass_var),
        ]
        for row, (label, var) in enumerate(fields):
            ttk.Label(frame, text=label, style="Surface.TLabel").grid(row=row, column=0, sticky="w", pady=4)
            show = "*" if label == "Password:" else ""
            ttk.Entry(frame, textvariable=var, width=36, show=show).grid(
                row=row, column=1, sticky="ew", pady=4
            )

        ttk.Label(frame, text="Private key:", style="Surface.TLabel").grid(row=5, column=0, sticky="w", pady=4)
        key_frame = ttk.Frame(frame, style="Surface.TFrame")
        key_frame.grid(row=5, column=1, sticky="ew", pady=4)
        ttk.Entry(key_frame, textvariable=self.key_var, width=28).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(key_frame, text="Browse...", command=self._browse_key).pack(
            side=tk.LEFT, padx=(6, 0)
        )

        btn_frame = ttk.Frame(frame, style="Surface.TFrame")
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(16, 0), sticky="e")
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btn_frame, text="Save", style="Primary.TButton", command=self._save).pack(side=tk.RIGHT)

        self.transient(parent)
        self.grab_set()
        self.wait_visibility()

    def _browse_key(self) -> None:
        path = filedialog.askopenfilename(title="Select private key")
        if path:
            self.key_var.set(path)

    def _save(self) -> None:
        try:
            port = int(self.port_var.get())
        except ValueError:
            port = 22
        self.result = SshSession(
            name=self.name_var.get().strip(),
            host=self.host_var.get().strip(),
            port=port,
            username=self.user_var.get().strip(),
            password=self.pass_var.get(),
            key_file=self.key_var.get().strip(),
        )
        self.destroy()
