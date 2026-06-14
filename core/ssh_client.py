"""SSH and SFTP connection management via paramiko."""

from __future__ import annotations

import stat
from dataclasses import dataclass
from typing import List, Optional

import paramiko

from core.session_store import SshSession


@dataclass
class RemoteEntry:
    name: str
    path: str
    is_dir: bool
    size: int = 0


class SshConnection:
    def __init__(self) -> None:
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        self.shell_channel = None
        self.session: Optional[SshSession] = None

    @property
    def connected(self) -> bool:
        return self.client is not None and self.client.get_transport() is not None

    def connect(self, session: SshSession) -> None:
        self.disconnect()
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": session.host,
            "port": session.port,
            "username": session.username,
            "timeout": 15,
            "allow_agent": True,
            "look_for_keys": True,
        }
        if session.password:
            connect_kwargs["password"] = session.password
        if session.key_file:
            connect_kwargs["key_filename"] = session.key_file

        client.connect(**connect_kwargs)
        self.client = client
        self.sftp = client.open_sftp()
        self.session = session

    def disconnect(self) -> None:
        if self.shell_channel is not None:
            try:
                self.shell_channel.close()
            except Exception:
                pass
            self.shell_channel = None
        if self.sftp is not None:
            try:
                self.sftp.close()
            except Exception:
                pass
            self.sftp = None
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
        self.session = None

    def open_shell(self) -> paramiko.Channel:
        if not self.client:
            raise RuntimeError("Not connected")
        if self.shell_channel is None or self.shell_channel.closed:
            self.shell_channel = self.client.invoke_shell(
                term="xterm", width=120, height=40
            )
            self.shell_channel.settimeout(0.0)
        return self.shell_channel

    def resize_shell(self, width: int, height: int) -> None:
        if self.shell_channel and not self.shell_channel.closed:
            self.shell_channel.resize_pty(width=max(width, 10), height=max(height, 5))

    def list_dir(self, path: str) -> List[RemoteEntry]:
        if not self.sftp:
            raise RuntimeError("SFTP not available")
        entries: List[RemoteEntry] = []
        for attr in self.sftp.listdir_attr(path):
            full_path = path.rstrip("/") + "/" + attr.filename
            if path == "/":
                full_path = "/" + attr.filename
            is_dir = stat.S_ISDIR(attr.st_mode)
            entries.append(
                RemoteEntry(
                    name=attr.filename,
                    path=full_path,
                    is_dir=is_dir,
                    size=attr.st_size or 0,
                )
            )
        entries.sort(key=lambda e: (not e.is_dir, e.name.lower()))
        return entries

    def getcwd(self) -> str:
        if not self.sftp:
            raise RuntimeError("SFTP not available")
        return self.sftp.normalize(".")

    def upload(self, local_path: str, remote_path: str) -> None:
        if not self.sftp:
            raise RuntimeError("SFTP not available")
        self.sftp.put(local_path, remote_path)

    def download(self, remote_path: str, local_path: str) -> None:
        if not self.sftp:
            raise RuntimeError("SFTP not available")
        self.sftp.get(remote_path, local_path)
