"""Main MobaxterN application window."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from core.session_store import SessionStore, SshSession
from core.settings_store import AppSettings, SettingsStore
from core.ssh_client import SshConnection
from ui.session_dialog import SessionDialog
from ui.sftp_panel import SftpPanel
from ui.terminal_widget import TerminalWidget
from ui.theme import apply_theme, canvas_bg

SIDEBAR_MIN_WIDTH = 260


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MobaxterN")
        self.geometry("1200x750")
        self.minsize(900, 600)

        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.dark_mode_var = tk.BooleanVar(value=self.settings.dark_mode)
        self.style = apply_theme(self, dark=self.settings.dark_mode)

        self.store = SessionStore()
        self.sessions: list[SshSession] = self.store.load()
        self.connection = SshConnection()
        self._connected_session_name: str | None = None
        self._selected_session_obj: SshSession | None = None
        self._selected_row: ttk.Frame | None = None
        self._terminal_widget: TerminalWidget | None = None
        self._sftp_widget: SftpPanel | None = None

        self._build_menu()
        self._build_ui()
        self._refresh_session_list()
        self.status_var = tk.StringVar(value="Ready — add or select a session to connect")
        ttk.Label(self, textvariable=self.status_var, style="Status.TLabel", anchor="w").pack(
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
        file_menu.add_checkbutton(
            label="Dark Mode",
            variable=self.dark_mode_var,
            command=self._on_dark_mode_toggle,
        )
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.destroy)

        session_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Session", menu=session_menu)
        session_menu.add_command(label="Connect", command=self._connect_selected)
        session_menu.add_command(label="Disconnect", command=self._disconnect)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(
            label="Dark Mode",
            variable=self.dark_mode_var,
            command=self._on_dark_mode_toggle,
        )

    def _on_dark_mode_toggle(self) -> None:
        self.settings_store.save(AppSettings(dark_mode=self.dark_mode_var.get()))
        self._apply_appearance()

    def _apply_appearance(self) -> None:
        self.style = apply_theme(self, dark=self.dark_mode_var.get())
        self.session_canvas.configure(bg=canvas_bg())
        was_connected = self.connection.connected
        self._refresh_session_list()
        if was_connected:
            self._mount_workspace()
        else:
            self._show_placeholders()

    def _build_ui(self) -> None:
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.paned.bind("<ButtonRelease-1>", self._enforce_sidebar_width)
        self.paned.bind("<B1-Motion>", self._enforce_sidebar_width)

        self.left_panel = ttk.Frame(self.paned, style="Sidebar.TFrame", width=SIDEBAR_MIN_WIDTH)
        self.left_panel.pack_propagate(False)
        self.paned.add(self.left_panel, weight=0)

        left = self.left_panel

        header = ttk.Frame(left, style="Sidebar.TFrame")
        header.pack(fill=tk.X, padx=10, pady=(8, 6))
        ttk.Label(header, text="Saved Sessions", style="Heading.TLabel").pack(side=tk.LEFT)
        self.dark_mode_btn = ttk.Checkbutton(
            header,
            text="Dark",
            variable=self.dark_mode_var,
            command=self._on_dark_mode_toggle,
            style="Toolbutton",
        )
        self.dark_mode_btn.pack(side=tk.RIGHT)

        list_frame = ttk.Frame(left, style="Sidebar.TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8)
        self.session_canvas = tk.Canvas(
            list_frame, highlightthickness=0, borderwidth=0, bg=canvas_bg()
        )
        self.session_scroll = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.session_canvas.yview
        )
        self.session_container = ttk.Frame(self.session_canvas, style="Sidebar.TFrame")
        self.session_container.bind(
            "<Configure>",
            lambda _e: self.session_canvas.configure(scrollregion=self.session_canvas.bbox("all")),
        )
        self._session_canvas_window = self.session_canvas.create_window(
            (0, 0), window=self.session_container, anchor="nw"
        )
        self.session_canvas.configure(yscrollcommand=self.session_scroll.set)
        self.session_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.session_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.session_canvas.bind(
            "<Configure>",
            lambda e: self.session_canvas.itemconfigure(
                self._session_canvas_window,
                width=max(e.width, SIDEBAR_MIN_WIDTH - 24),
            ),
        )
        self.session_canvas.bind("<Enter>", self._bind_session_scroll)
        self.session_canvas.bind("<Leave>", self._unbind_session_scroll)

        btn_frame = ttk.Frame(left, style="Sidebar.TFrame")
        btn_frame.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(
            btn_frame, text="New", style="Primary.TButton", command=self._new_session
        ).pack(fill=tk.X)

        right = ttk.Frame(self.paned)
        self.paned.add(right, weight=1)

        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.terminal_frame = ttk.Frame(self.notebook)
        self.sftp_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.terminal_frame, text="Command Line")
        self.notebook.add(self.sftp_frame, text="SFTP")

        self._show_placeholders()
        self.after(100, self._enforce_sidebar_width)

    def _enforce_sidebar_width(self, _event=None) -> None:
        try:
            if self.paned.sashpos(0) < SIDEBAR_MIN_WIDTH:
                self.paned.sashpos(0, SIDEBAR_MIN_WIDTH)
        except tk.TclError:
            pass

    def _show_placeholders(self) -> None:
        for frame, msg in (
            (self.terminal_frame, "Connect to a session to open the command line tab."),
            (self.sftp_frame, "Connect to a session to browse remote files via SFTP."),
        ):
            for child in frame.winfo_children():
                child.destroy()
            ttk.Label(frame, text=msg, style="Muted.TLabel").pack(expand=True)

    def _bind_session_scroll(self, _event=None) -> None:
        self.session_canvas.bind_all("<MouseWheel>", self._on_session_mousewheel)
        self.session_canvas.bind_all("<Button-4>", self._on_session_mousewheel_linux)
        self.session_canvas.bind_all("<Button-5>", self._on_session_mousewheel_linux)

    def _unbind_session_scroll(self, _event=None) -> None:
        self.session_canvas.unbind_all("<MouseWheel>")
        self.session_canvas.unbind_all("<Button-4>")
        self.session_canvas.unbind_all("<Button-5>")

    def _on_session_mousewheel(self, event) -> None:
        if self.session_canvas.winfo_exists():
            self.session_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _on_session_mousewheel_linux(self, event) -> None:
        if self.session_canvas.winfo_exists():
            delta = -1 if event.num == 4 else 1
            self.session_canvas.yview_scroll(delta, "units")

    def _refresh_session_list(self) -> None:
        selected_name = self._selected_session_obj.name if self._selected_session_obj else None
        for child in self.session_container.winfo_children():
            child.destroy()
        self._selected_row = None
        self._selected_session_obj = None

        if not self.sessions:
            ttk.Label(
                self.session_container,
                text="No sessions yet.\nClick New to add one.",
                style="SidebarMuted.TLabel",
                justify=tk.CENTER,
            ).pack(pady=24, padx=12)
            return

        for session in self.sessions:
            self._add_session_row(session, selected_name)

    def _add_session_row(self, session: SshSession, selected_name: str | None = None) -> None:
        is_selected = selected_name == session.name
        is_connected = self._connected_session_name == session.name
        prefix = "Selected." if is_selected else "Connected." if is_connected else ""

        row = ttk.Frame(self.session_container, style=f"{prefix}Session.TFrame" if prefix else "Session.TFrame")
        row.pack(fill=tk.X, pady=4, padx=2)

        inner = ttk.Frame(row, style=f"{prefix}SessionInner.TFrame")
        inner.pack(fill=tk.X, padx=6, pady=6)
        inner.columnconfigure(0, weight=1)

        title_row = ttk.Frame(inner, style=f"{prefix}SessionInner.TFrame")
        title_row.grid(row=0, column=0, columnspan=2, sticky="ew")
        title_row.columnconfigure(0, weight=1)

        ttk.Label(
            title_row,
            text=session.name,
            style=f"{prefix}SessionName.TLabel" if prefix else "SessionName.TLabel",
        ).grid(row=0, column=0, sticky="w")

        if is_connected:
            ttk.Label(
                title_row,
                text="Connected",
                style=f"{prefix}SessionBadge.TLabel" if prefix else "SessionBadge.TLabel",
            ).grid(row=0, column=1, sticky="e", padx=(8, 0))

        ttk.Label(
            inner,
            text=f"{session.username}@{session.host}:{session.port}",
            style=f"{prefix}SessionSub.TLabel" if prefix else "SessionSub.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        actions = ttk.Frame(inner, style=f"{prefix}SessionInner.TFrame")
        actions.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        if is_connected:
            ttk.Button(
                actions, text="Disconnect", width=8, style="Small.TButton",
                command=lambda s=session: self._disconnect_session(s),
            ).pack(side=tk.LEFT, padx=(0, 3))
        else:
            ttk.Button(
                actions, text="Connect", width=7, style="Primary.TButton",
                command=lambda s=session: self._connect_session(s),
            ).pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(
            actions, text="Edit", width=6, style="Small.TButton",
            command=lambda s=session: self._edit_session_direct(s),
        ).pack(side=tk.LEFT, padx=3)
        ttk.Button(
            actions, text="Delete", width=6, style="Danger.TButton",
            command=lambda s=session: self._delete_session_direct(s),
        ).pack(side=tk.LEFT)

        row._session = session  # type: ignore[attr-defined]
        row._inner = inner  # type: ignore[attr-defined]

        for widget in (row, inner, title_row):
            widget.bind("<Button-1>", lambda _e, s=session, r=row: self._select_session_row(s, r))
            widget.bind("<Double-Button-1>", lambda _e, s=session: self._connect_session(s))
        for child in inner.winfo_children():
            if isinstance(child, ttk.Label):
                child.bind("<Button-1>", lambda _e, s=session, r=row: self._select_session_row(s, r))
                child.bind("<Double-Button-1>", lambda _e, s=session: self._connect_session(s))

        if is_selected:
            self._selected_session_obj = session
            self._selected_row = row

    def _select_session_row(self, session: SshSession, row: ttk.Frame) -> None:
        if self._selected_row is not None and self._selected_row is not row:
            self._restyle_row(self._selected_row)
        self._selected_session_obj = session
        self._selected_row = row
        self._set_row_prefix(row, "Selected.")

    def _restyle_row(self, row: ttk.Frame) -> None:
        session: SshSession = row._session  # type: ignore[attr-defined]
        if self._connected_session_name == session.name:
            self._set_row_prefix(row, "Connected.")
        else:
            self._set_row_prefix(row, "")

    def _set_row_prefix(self, row: ttk.Frame, prefix: str) -> None:
        row.configure(style=f"{prefix}Session.TFrame" if prefix else "Session.TFrame")
        inner: ttk.Frame = row._inner  # type: ignore[attr-defined]
        inner.configure(style=f"{prefix}SessionInner.TFrame")
        for widget in inner.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.configure(style=f"{prefix}SessionInner.TFrame")
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Label):
                        self._apply_label_prefix(child, prefix)
            elif isinstance(widget, ttk.Label):
                self._apply_label_prefix(widget, prefix)

    def _apply_label_prefix(self, label: ttk.Label, prefix: str) -> None:
        style_name = str(label.cget("style"))
        if "SessionName" in style_name:
            label.configure(style=f"{prefix}SessionName.TLabel" if prefix else "SessionName.TLabel")
        elif "SessionSub" in style_name:
            label.configure(style=f"{prefix}SessionSub.TLabel" if prefix else "SessionSub.TLabel")
        elif "SessionBadge" in style_name:
            label.configure(style=f"{prefix}SessionBadge.TLabel" if prefix else "SessionBadge.TLabel")

    def _selected_session(self) -> SshSession | None:
        return self._selected_session_obj

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
        self._edit_session_direct(session)

    def _edit_session_direct(self, session: SshSession) -> None:
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
            if self._connected_session_name == session.name:
                self._connected_session_name = updated.name
        self.sessions = self.store.upsert(updated)
        self._selected_session_obj = updated
        self._refresh_session_list()
        self.status_var.set(f"Updated session: {updated.name}")

    def _delete_session(self) -> None:
        session = self._selected_session()
        if not session:
            messagebox.showinfo("Delete Session", "Select a session first.")
            return
        self._delete_session_direct(session)

    def _delete_session_direct(self, session: SshSession) -> None:
        if not messagebox.askyesno(
            "Delete Session",
            f'Delete session "{session.name}" ({session.username}@{session.host})?',
            parent=self,
        ):
            return
        self.sessions = self.store.delete(session.name)
        if self._selected_session_obj and self._selected_session_obj.name == session.name:
            self._selected_session_obj = None
        self._refresh_session_list()
        if self._connected_session_name == session.name:
            self._disconnect()
        self.status_var.set(f"Deleted session: {session.name}")

    def _connect_selected(self) -> None:
        session = self._selected_session()
        if not session:
            messagebox.showinfo("Connect", "Select a session first.")
            return
        self._connect_session(session)

    def _connect_session(self, session: SshSession) -> None:
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
        self._selected_session_obj = session
        self._mount_workspace()
        self._refresh_session_list()
        self.status_var.set(f"Connected to {session.username}@{session.host}:{session.port}")

    def _disconnect_session(self, session: SshSession) -> None:
        if self._connected_session_name != session.name:
            return
        self._disconnect()

    def _disconnect(self) -> None:
        self.connection.disconnect()
        self._connected_session_name = None
        self._terminal_widget = None
        self._sftp_widget = None
        self._show_placeholders()
        self.status_var.set("Disconnected")
        self._refresh_session_list()

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
