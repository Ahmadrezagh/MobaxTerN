"""Shared MobaxterN UI theme and ttk styles."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

LIGHT_COLORS = {
    "bg": "#f4f4f5",
    "sidebar": "#ebebed",
    "surface": "#ffffff",
    "border": "#d4d4d8",
    "text": "#18181b",
    "muted": "#71717a",
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "row": "#ffffff",
    "row_hover": "#f8fafc",
    "row_selected": "#dbeafe",
    "row_connected": "#dcfce7",
    "danger": "#dc2626",
    "success": "#16a34a",
    "terminal_bg": "#1e1e1e",
    "terminal_fg": "#d4d4d4",
}

DARK_COLORS = {
    "bg": "#18181b",
    "sidebar": "#27272a",
    "surface": "#3f3f46",
    "border": "#52525b",
    "text": "#fafafa",
    "muted": "#a1a1aa",
    "primary": "#3b82f6",
    "primary_hover": "#2563eb",
    "row": "#3f3f46",
    "row_hover": "#52525b",
    "row_selected": "#1e3a5f",
    "row_connected": "#14532d",
    "danger": "#f87171",
    "success": "#4ade80",
    "terminal_bg": "#1e1e1e",
    "terminal_fg": "#d4d4d4",
}

COLORS = dict(LIGHT_COLORS)


def set_dark_mode(enabled: bool) -> None:
    global COLORS
    COLORS = dict(DARK_COLORS if enabled else LIGHT_COLORS)


def is_dark_mode() -> bool:
    return COLORS["bg"] == DARK_COLORS["bg"]


def apply_theme(root: tk.Misc, *, dark: bool = False) -> ttk.Style:
    set_dark_mode(dark)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    c = COLORS
    root.configure(bg=c["bg"])

    style.configure(".", background=c["bg"], foreground=c["text"])
    style.configure("TFrame", background=c["bg"])
    style.configure("Sidebar.TFrame", background=c["sidebar"])
    style.configure("Surface.TFrame", background=c["surface"])
    style.configure("Surface.TLabel", background=c["surface"], foreground=c["text"])
    style.configure("TLabel", background=c["bg"], foreground=c["text"])
    style.configure("Sidebar.TLabel", background=c["sidebar"], foreground=c["text"])
    style.configure("Muted.TLabel", background=c["bg"], foreground=c["muted"])
    style.configure("SidebarMuted.TLabel", background=c["sidebar"], foreground=c["muted"])
    style.configure("Heading.TLabel", background=c["sidebar"], foreground=c["text"], font=("", 12, "bold"))

    style.configure(
        "TButton",
        padding=(8, 4),
        background=c["surface"],
        foreground=c["text"],
        borderwidth=1,
        focusthickness=0,
        font=("", 10),
    )
    style.map(
        "TButton",
        background=[("active", c["row_hover"]), ("pressed", c["border"])],
        relief=[("pressed", "sunken"), ("!pressed", "raised")],
    )
    style.configure(
        "Primary.TButton",
        background=c["primary"],
        foreground="#ffffff",
        borderwidth=0,
        padding=(6, 3),
        font=("", 9),
    )
    style.map(
        "Primary.TButton",
        background=[("active", c["primary_hover"]), ("disabled", c["border"])],
        foreground=[("disabled", c["muted"])],
    )
    style.configure("Compact.TButton", padding=(6, 3), font=("", 9))
    style.configure("Small.TButton", padding=(5, 2), font=("", 9))
    style.configure("Danger.TButton", padding=(5, 2), font=("", 9), foreground=c["danger"])
    style.configure("Success.TButton", padding=(5, 2), font=("", 9), foreground=c["success"])
    style.configure("Toolbutton", padding=(6, 3), font=("", 9))
    style.map("Toolbutton", background=[("selected", c["row_selected"]), ("active", c["row_hover"])])

    style.configure("TEntry", fieldbackground=c["surface"], foreground=c["text"], padding=4)
    style.configure("TNotebook", background=c["bg"], borderwidth=0)
    style.configure("TNotebook.Tab", padding=(10, 6), background=c["sidebar"], foreground=c["text"])
    style.map("TNotebook.Tab", background=[("selected", c["surface"])])
    style.configure("TPanedwindow", background=c["bg"])
    style.configure("Vertical.TScrollbar", background=c["sidebar"], troughcolor=c["bg"])
    style.configure("Treeview", background=c["surface"], fieldbackground=c["surface"], foreground=c["text"])
    style.configure("Treeview.Heading", background=c["sidebar"], foreground=c["text"])

    _configure_session_styles(style, c["row"], c["text"], c["muted"], c["success"])
    _configure_session_styles(style, c["row_selected"], c["text"], c["muted"], c["success"], prefix="Selected")
    _configure_session_styles(style, c["row_connected"], c["text"], c["muted"], c["success"], prefix="Connected")

    style.configure("Session.TFrame", background=c["row"], borderwidth=1, relief="solid")
    style.configure("Selected.Session.TFrame", background=c["row_selected"])
    style.configure("Connected.Session.TFrame", background=c["row_connected"])
    style.configure("Status.TLabel", background=c["sidebar"], foreground=c["muted"], padding=(8, 4))
    return style


def _configure_session_styles(
    style: ttk.Style,
    bg: str,
    text: str,
    muted: str,
    success: str,
    prefix: str = "",
) -> None:
    p = f"{prefix}." if prefix else ""
    style.configure(f"{p}SessionInner.TFrame", background=bg)
    style.configure(f"{p}SessionName.TLabel", background=bg, foreground=text, font=("", 10, "bold"))
    style.configure(f"{p}SessionSub.TLabel", background=bg, foreground=muted, font=("", 9))
    style.configure(f"{p}SessionBadge.TLabel", background=bg, foreground=success, font=("", 9, "bold"))


def canvas_bg() -> str:
    return COLORS["sidebar"]
