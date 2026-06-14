"""Persist application settings."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AppSettings:
    dark_mode: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        return cls(dark_mode=bool(data.get("dark_mode", False)))


class SettingsStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        if path is None:
            path = Path.home() / ".mobaxtern" / "settings.json"
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return AppSettings()
        if not isinstance(raw, dict):
            return AppSettings()
        return AppSettings.from_dict(raw)

    def save(self, settings: AppSettings) -> None:
        self.path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
