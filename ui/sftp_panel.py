"""SFTP directory tree with path bar and file transfer."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from core.ssh_client import RemoteEntry, SshConnection


class SftpPanel(ttk.Frame):
    def __init__(self, parent, connection: SshConnection, *, compact: bool = False) -> None:
        super().__init__(parent)
        self.connection = connection
        self.compact = compact
        try:
            self.current_path = connection.getcwd()
        except Exception:
            self.current_path = "."

        ttk.Label(self, text="Remote path:", style="Sidebar.TLabel" if compact else "TLabel").pack(
            anchor="w", padx=4, pady=(4, 0)
        )
        self.path_var = tk.StringVar(value=self.current_path)
        path_row = ttk.Frame(self)
        path_row.pack(fill=tk.X, padx=4, pady=4)
        self.path_entry = ttk.Entry(path_row, textvariable=self.path_var)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.path_entry.bind("<Return>", self._on_path_enter)
        ttk.Button(path_row, text="Go", style="Small.TButton", command=self._go_to_entered_path).pack(
            side=tk.LEFT, padx=(4, 0)
        )

        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=4, pady=4)
        if compact:
            row1 = ttk.Frame(toolbar)
            row1.pack(fill=tk.X)
            ttk.Button(row1, text="Up", style="Small.TButton", command=self._go_up).pack(
                side="left", padx=1, fill=tk.X, expand=True
            )
            ttk.Button(row1, text="Refresh", style="Small.TButton", command=self.refresh).pack(
                side="left", padx=1, fill=tk.X, expand=True
            )
            row2 = ttk.Frame(toolbar)
            row2.pack(fill=tk.X, pady=(4, 0))
            ttk.Button(row2, text="Upload", style="Small.TButton", command=self.upload_files).pack(
                side="left", padx=1, fill=tk.X, expand=True
            )
            ttk.Button(row2, text="Download", style="Small.TButton", command=self.download_files).pack(
                side="left", padx=1, fill=tk.X, expand=True
            )
        else:
            ttk.Button(toolbar, text="Up", command=self._go_up).pack(side="left", padx=2)
            ttk.Button(toolbar, text="Refresh", command=self.refresh).pack(side="left", padx=2)
            ttk.Button(toolbar, text="Upload", command=self.upload_files).pack(side="left", padx=2)
            ttk.Button(toolbar, text="Download", command=self.download_files).pack(side="left", padx=2)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=4, pady=4)

        name_w = 110 if compact else 220
        self.tree = ttk.Treeview(
            tree_frame, columns=("size", "type"), show="tree headings", selectmode="extended"
        )
        self.tree.heading("#0", text="Name")
        self.tree.heading("size", text="Size")
        self.tree.heading("type", text="Type")
        self.tree.column("#0", width=name_w)
        self.tree.column("size", width=48 if compact else 80)
        self.tree.column("type", width=48 if compact else 80)
        self.tree.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<Double-1>", self._on_double_click)

        self.refresh()

    def _set_path(self, path: str) -> None:
        self.current_path = path or "."
        self.path_var.set(self.current_path)
        self.refresh()

    def _on_path_enter(self, _event=None) -> str:
        self._go_to_entered_path()
        return "break"

    def _go_to_entered_path(self) -> None:
        path = self.path_var.get().strip()
        if not path:
            self.path_var.set(self.current_path)
            return
        try:
            if self.connection.sftp:
                path = self.connection.sftp.normalize(path)
            self.connection.list_dir(path)
        except Exception as exc:
            messagebox.showwarning("SFTP Error", str(exc), parent=self)
            self.path_var.set(self.current_path)
            return
        self.current_path = path
        self.path_var.set(self.current_path)
        self.refresh()

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            entries = self.connection.list_dir(self.current_path)
        except Exception as exc:
            messagebox.showwarning("SFTP Error", str(exc), parent=self)
            return
        for entry in entries:
            self._add_entry(entry)

    def _add_entry(self, entry: RemoteEntry) -> None:
        size = "" if entry.is_dir else self._format_size(entry.size)
        kind = "Directory" if entry.is_dir else "File"
        self.tree.insert(
            "", "end", text=entry.name, values=(size, kind), tags=(entry.path, str(entry.is_dir))
        )

    @staticmethod
    def _format_size(size: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _on_double_click(self, _event) -> None:
        item = self.tree.focus()
        if not item:
            return
        tags = self.tree.item(item, "tags")
        if len(tags) < 2:
            return
        remote_path, is_dir = tags[0], tags[1] == "True"
        if is_dir:
            self._set_path(remote_path)
        else:
            self._download_file(remote_path, self.tree.item(item, "text"))

    def _download_file(self, remote_path: str, name: str) -> None:
        local = filedialog.asksaveasfilename(
            title="Save file as",
            initialfile=name,
            parent=self,
        )
        if not local:
            return
        try:
            self.connection.download(remote_path, local)
        except Exception as exc:
            messagebox.showwarning("Download error", str(exc), parent=self)
            return
        messagebox.showinfo("Download", f"Downloaded {name} to {local}.", parent=self)

    def _go_up(self) -> None:
        if self.current_path in ("/", ".", ""):
            return
        parent = str(Path(self.current_path).parent)
        if parent == ".":
            parent = "/"
        self._set_path(parent)

    def upload_files(self) -> None:
        files = filedialog.askopenfilenames(title="Upload files", parent=self)
        if not files:
            return
        errors = []
        for local in files:
            remote = self.current_path.rstrip("/") + "/" + Path(local).name
            if self.current_path == "/":
                remote = "/" + Path(local).name
            try:
                self.connection.upload(local, remote)
            except Exception as exc:
                errors.append(f"{Path(local).name}: {exc}")
        self.refresh()
        if errors:
            messagebox.showwarning("Upload errors", "\n".join(errors), parent=self)
        else:
            messagebox.showinfo("Upload", f"Uploaded {len(files)} file(s).", parent=self)

    def download_files(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Download", "Select one or more files to download.", parent=self)
            return
        files = [item for item in selected if self.tree.item(item, "tags")[1] == "False"]
        if not files:
            messagebox.showinfo("Download", "Select files (not directories).", parent=self)
            return
        dest = filedialog.askdirectory(title="Save to directory", parent=self)
        if not dest:
            return
        errors = []
        for item in files:
            name = self.tree.item(item, "text")
            remote = self.tree.item(item, "tags")[0]
            local = str(Path(dest) / name)
            try:
                self.connection.download(remote, local)
            except Exception as exc:
                errors.append(f"{name}: {exc}")
        if errors:
            messagebox.showwarning("Download errors", "\n".join(errors), parent=self)
        elif len(files) == 1:
            messagebox.showinfo(
                "Download", f"Downloaded {self.tree.item(files[0], 'text')} to {dest}.", parent=self
            )
        else:
            messagebox.showinfo(
                "Download", f"Downloaded {len(files)} file(s) to {dest}.", parent=self
            )
