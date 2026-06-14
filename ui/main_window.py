"""Main MobaxterN application window."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from core.session_store import SessionStore, SshSession
from core.ssh_client import SshConnection
from ui.session_dialog import SessionDialog
from ui.sftp_panel import SftpPanel
from ui.terminal_widget import TerminalWidget


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MobaxterN")
        self.geometry("1200x750")
        self.minsize(900, 600)

        self.store = SessionStore()
        self.sessions: list[SshSession] = self.store.load()
        self.connection = SshConnection()
        self._connected_session_name: str | None = None
        self._terminal_widget: TerminalWidget | None = None
        self._sftp_widget: SftpPanel | None = None

        self._build_menu()
        self._build_ui()
        self._refresh_session_list()
        self.status_var = tk.StringVar(value="Ready — add or select a session to connect")
        ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w").pack(
            fill=tk.X, side=tk.BOTTOM
        )

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session...", command=self._new_session)
        file_menu.add_command(label="Edit Session...", command=self._edit_session)
        file_menu.add_command(label="Delete Session", command=self._delete_session)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.destroy)

        session_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Session", menu=session_menu)
        session_menu.add_command(label="Connect", command=self._connect_selected)
        session_menu.add_command(label="Disconnect", command=self._disconnect)

    def _build_ui(self) -> None:
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Left: saved sessions
        left = ttk.Frame(paned, width=240)
        paned.add(left, weight=0)
        ttk.Label(left, text="Saved Sessions", font=("", 11, "bold")).pack(
            anchor="w", padx=4, pady=(0, 4)
        )

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.session_list = tk.Listbox(list_frame, width=30, activestyle="dotbox")
        self.session_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.session_list.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.session_list.configure(yscrollcommand=scroll.set)
        self.session_list.bind("<Double-Button-1>", lambda _e: self._connect_selected())

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=8)
        ttk.Button(btn_frame, text="New", command=self._new_session).pack(
            side=tk.LEFT, padx=2, fill=tk.X, expand=True
        )
        ttk.Button(btn_frame, text="Connect", command=self._connect_selected).pack(
            side=tk.LEFT, padx=2, fill=tk.X, expand=True
        )
        ttk.Button(btn_frame, text="Disconnect", command=self._disconnect).pack(
            side=tk.LEFT, padx=2, fill=tk.X, expand=True
        )

        # Right: tabs
        right = ttk.Frame(paned)
        paned.add(right, weight=1)

        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.terminal_frame = ttk.Frame(self.notebook)
        self.sftp_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.terminal_frame, text="Command Line")
        self.notebook.add(self.sftp_frame, text="SFTP")

        self._show_placeholders()

    def _show_placeholders(self) -> None:
        for frame, msg in (
            (self.terminal_frame, "Connect to a session to open the command line tab."),
            (self.sftp_frame, "Connect to a session to browse remote files via SFTP."),
        ):
            for child in frame.winfo_children():
                child.destroy()
            ttk.Label(frame, text=msg, foreground="#888").pack(expand=True)

    def _refresh_session_list(self) -> None:
        self.session_list.delete(0, tk.END)
        for session in self.sessions:
            self.session_list.insert(
                tk.END, f"{session.name}  ({session.username}@{session.host})"
            )

    def _selected_session(self) -> SshSession | None:
        sel = self.session_list.curselection()
        if not sel:
            return None
        index = sel[0]
        if index >= len(self.sessions):
            return None
        return self.sessions[index]

    def _new_session(self) -> None:
        dialog = SessionDialog(self)
        self.wait_window(dialog)
        if not dialog.result:
            return
        session = dialog.result
        if not session.name or not session.host or not session.username:
            messagebox.showwarning("Validation", "Name, host, and username are required.")
            return
        self.sessions = self.store.upsert(session)
        self._refresh_session_list()
        self.status_var.set(f"Saved session: {session.name}")

    def _edit_session(self) -> None:
        session = self._selected_session()
        if not session:
            messagebox.showinfo("Edit Session", "Select a session first.")
            return
        dialog = SessionDialog(self, session)
        self.wait_window(dialog)
        if not dialog.result:
            return
        updated = dialog.result
        if not updated.name or not updated.host or not updated.username:
            messagebox.showwarning("Validation", "Name, host, and username are required.")
            return
        if updated.name != session.name:
            self.sessions = self.store.delete(session.name)
        self.sessions = self.store.upsert(updated)
        self._refresh_session_list()
        self.status_var.set(f"Updated session: {updated.name}")

    def _delete_session(self) -> None:
        session = self._selected_session()
        if not session:
            messagebox.showinfo("Delete Session", "Select a session first.")
            return
        confirm = simpledialog.askstring(
            "Confirm delete",
            f'Type "{session.name}" to delete this session:',
            parent=self,
        )
        if confirm != session.name:
            return
        self.sessions = self.store.delete(session.name)
        self._refresh_session_list()
        if self._connected_session_name == session.name:
            self._disconnect()
        self.status_var.set(f"Deleted session: {session.name}")

    def _connect_selected(self) -> None:
        session = self._selected_session()
        if not session:
            messagebox.showinfo("Connect", "Select a session first.")
            return
        if self.connection.connected and self._connected_session_name == session.name:
            self.status_var.set(f"Already connected to {session.name}")
            return

        self.status_var.set(f"Connecting to {session.host}...")
        self.update_idletasks()
        try:
            self.connection.connect(session)
        except Exception as exc:
            messagebox.showerror("Connection failed", str(exc))
            self.status_var.set("Connection failed")
            return

        self._connected_session_name = session.name
        self._mount_workspace()
        self.status_var.set(
            f"Connected to {session.username}@{session.host}:{session.port}"
        )

    def _disconnect(self) -> None:
        self.connection.disconnect()
        self._connected_session_name = None
        self._terminal_widget = None
        self._sftp_widget = None
        self._show_placeholders()
        self.status_var.set("Disconnected")

    def _mount_workspace(self) -> None:
        for child in self.terminal_frame.winfo_children():
            child.destroy()
        for child in self.sftp_frame.winfo_children():
            child.destroy()

        self._terminal_widget = TerminalWidget(self.terminal_frame, self.connection)
        self._terminal_widget.pack(fill=tk.BOTH, expand=True)

        self._sftp_widget = SftpPanel(self.sftp_frame, self.connection)
        self._sftp_widget.pack(fill=tk.BOTH, expand=True)

    def destroy(self) -> None:
        self.connection.disconnect()
        super().destroy()
