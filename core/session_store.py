"""Persist SSH session profiles to disk."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class SshSession:
    name: str
    host: str
    port: int = 22
    username: str = ""
    password: str = ""
    key_file: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "SshSession":
        return cls(
            name=data.get("name", ""),
            host=data.get("host", ""),
            port=int(data.get("port", 22)),
            username=data.get("username", ""),
            password=data.get("password", ""),
            key_file=data.get("key_file", ""),
        )


class SessionStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        if path is None:
            path = Path.home() / ".mobaxtern" / "sessions.json"
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> List[SshSession]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        if not isinstance(raw, list):
            return []
        return [SshSession.from_dict(item) for item in raw if isinstance(item, dict)]

    def save(self, sessions: List[SshSession]) -> None:
        payload = [asdict(s) for s in sessions]
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def upsert(self, session: SshSession) -> List[SshSession]:
        sessions = self.load()
        replaced = False
        for i, existing in enumerate(sessions):
            if existing.name == session.name:
                sessions[i] = session
                replaced = True
                break
        if not replaced:
            sessions.append(session)
        self.save(sessions)
        return sessions

    def delete(self, name: str) -> List[SshSession]:
        sessions = [s for s in self.load() if s.name != name]
        self.save(sessions)
        return sessions
