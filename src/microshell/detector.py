from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class Shell(Enum):
    POWERSHELL = "powershell"
    CMD = "cmd"


@dataclass(frozen=True)
class ShellInfo:
    dialect: Shell
    major: int = 7
    minor: int = 0

    @property
    def supports_and_or(self) -> bool:
        """PowerShell 7+ 原生支持 && / ||。"""
        return self.dialect is Shell.POWERSHELL and self.major >= 7

    @property
    def executable(self) -> str:
        if self.dialect is Shell.CMD:
            return "cmd"
        return "pwsh" if self.major >= 7 else "powershell"


_ALIASES: dict[str, ShellInfo] = {
    "pwsh": ShellInfo(Shell.POWERSHELL, 7, 4),
    "ps7": ShellInfo(Shell.POWERSHELL, 7, 4),
    "powershell7": ShellInfo(Shell.POWERSHELL, 7, 4),
    "powershell": ShellInfo(Shell.POWERSHELL, 5, 1),
    "ps": ShellInfo(Shell.POWERSHELL, 5, 1),
    "powershell5": ShellInfo(Shell.POWERSHELL, 5, 1),
    "cmd": ShellInfo(Shell.CMD, 10, 0),
    "cmd.exe": ShellInfo(Shell.CMD, 10, 0),
}


def resolve_shell_info(name: str | None) -> ShellInfo:
    if name is None:
        env = os.environ.get("MICROSHELL_SHELL", "").lower()
        if env:
            name = env
        else:
            # 默认 Windows PowerShell 5.1，因为 Windows 自带
            return _ALIASES["powershell"]
    name = name.lower()
    if name not in _ALIASES:
        raise ValueError(f"unknown shell: {name}")
    return _ALIASES[name]


def resolve_shell(name: str | None) -> Shell:
    return resolve_shell_info(name).dialect