"""Interactive SSH shell tab — single-pane terminal with remote echo."""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import scrolledtext, ttk

from core.ssh_client import SshConnection
from ui.theme import COLORS

_CLEAR_RE = re.compile(r"\x1b\[[0-9;]*2J|\x1b\[[0-9;]*3J|\x1bc|\x0c")
_ANSI_RE = re.compile(
    r"\x1b\[[0-9;]*[A-Za-z]"
    r"|\x1b\][^\x07]*\x07"
    r"|\x1b[\(\)][0-9A-Za-z]"
    r"|\x1b\[[\d;]*m"
)


class TerminalWidget(ttk.Frame):
    _KEY_BYTES = {
        "Return": b"\n",
        "BackSpace": b"\x7f",
        "Delete": b"\x1b[3~",
        "Tab": b"\t",
        "Escape": b"\x1b",
        "Up": b"\x1b[A",
        "Down": b"\x1b[B",
        "Right": b"\x1b[C",
        "Left": b"\x1b[D",
        "Home": b"\x1b[H",
        "End": b"\x1b[F",
        "Prior": b"\x1b[5~",
        "Next": b"\x1b[6~",
    }

    def __init__(self, parent, connection: SshConnection) -> None:
        super().__init__(parent)
        self.connection = connection
        self._ready = False

        self.screen = scrolledtext.ScrolledText(
            self,
            wrap=tk.NONE,
            bg=COLORS["terminal_bg"],
            fg=COLORS["terminal_fg"],
            insertbackground=COLORS["terminal_fg"],
            font=("Menlo", 11),
            undo=False,
            maxundo=0,
            borderwidth=0,
            highlightthickness=0,
        )
        self.screen.pack(fill=tk.BOTH, expand=True)
        self.screen.bind("<Key>", self._on_key)
        self.screen.bind("<Control-c>", self._on_ctrl_c)
        self.screen.bind("<Control-C>", self._on_ctrl_c)
        self.screen.bind("<Control-d>", self._on_ctrl_d)
        self.screen.bind("<Control-D>", self._on_ctrl_d)
        self.screen.bind("<Control-v>", self._on_paste)
        self.screen.bind("<Control-V>", self._on_paste)
        self.screen.bind("<Button-1>", self._on_click)
        self.screen.bind("<FocusIn>", self._keep_cursor_at_end)

        hint = ttk.Label(
            self,
            text="Type here like a real terminal · ↑↓ history · Ctrl+C stop · Ctrl+D exit",
            style="Muted.TLabel",
        )
        hint.pack(anchor="w", padx=6, pady=4)

        self.after(50, self._init_shell)
        self.after(50, self._poll_shell)

    def _init_shell(self) -> None:
        try:
            channel = self.connection.open_shell()
            if channel.recv_ready():
                data = channel.recv(65535).decode("utf-8", errors="replace")
                self._handle_remote_output(data)
            self._ready = True
            self.screen.focus_set()
            self._keep_cursor_at_end()
        except Exception as exc:
            self._append_text(f"\n[Connection error: {exc}]\n")

    def _on_click(self, _event=None) -> str:
        self.screen.focus_set()
        self._keep_cursor_at_end()
        return "break"

    def _keep_cursor_at_end(self, _event=None) -> None:
        self.screen.mark_set(tk.INSERT, tk.END)
        self.screen.see(tk.END)

    def _on_key(self, event) -> str:
        if not self._ready:
            return "break"

        self._keep_cursor_at_end()

        if event.keysym in self._KEY_BYTES:
            self._send_bytes(self._KEY_BYTES[event.keysym])
            return "break"

        if event.char and len(event.char) == 1 and event.char.isprintable():
            self._send_bytes(event.char.encode("utf-8"))
        return "break"

    def _on_ctrl_c(self, _event=None) -> str:
        self._send_bytes(b"\x03")
        return "break"

    def _on_ctrl_d(self, _event=None) -> str:
        self._send_bytes(b"\x04")
        return "break"

    def _on_paste(self, _event=None) -> str:
        try:
            text = self.clipboard_get()
        except tk.TclError:
            return "break"
        if text:
            self._send_bytes(text.encode("utf-8"))
        return "break"

    def _send_bytes(self, data: bytes) -> None:
        try:
            channel = self.connection.open_shell()
            channel.send(data)
        except Exception as exc:
            self._append_text(f"\n[Send error: {exc}]\n")

    def _poll_shell(self) -> None:
        if self._ready:
            try:
                channel = self.connection.open_shell()
                while channel.recv_ready():
                    data = channel.recv(65535).decode("utf-8", errors="replace")
                    self._handle_remote_output(data)
            except Exception:
                pass
        self.after(50, self._poll_shell)

    def _clear_screen(self) -> None:
        self.screen.delete("1.0", tk.END)

    def _strip_ansi(self, text: str) -> str:
        return _ANSI_RE.sub("", text)

    def _handle_remote_output(self, data: str) -> None:
        while data:
            match = _CLEAR_RE.search(data)
            if not match:
                clean = self._strip_ansi(data)
                if clean:
                    self._append_text(clean)
                break
            before = data[: match.start()]
            if before:
                clean = self._strip_ansi(before)
                if clean:
                    self._append_text(clean)
            self._clear_screen()
            data = data[match.end() :]

    def _append_text(self, text: str) -> None:
        self.screen.insert(tk.END, text)
        self._keep_cursor_at_end()
