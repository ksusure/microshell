from __future__ import annotations

import os
from enum import Enum


class Shell(Enum):
    POWERSHELL = "powershell"
    CMD = "cmd"


def detect_shell() -> Shell:
    # 第一阶段：默认 PowerShell，允许环境变量或 CLI 覆盖
    if os.environ.get("MICROSHELL_SHELL", "").lower() == "cmd":
        return Shell.CMD
    return Shell.POWERSHELL


def resolve_shell(name: str | None) -> Shell:
    if name is None:
        return detect_shell()
    name = name.lower()
    if name in ("powershell", "pwsh", "ps"):
        return Shell.POWERSHELL
    if name in ("cmd", "cmd.exe"):
        return Shell.CMD
    raise ValueError(f"unknown shell: {name}")