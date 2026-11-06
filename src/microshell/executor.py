from __future__ import annotations

import subprocess

from .detector import Shell, ShellInfo


def execute(command_line: str, si: ShellInfo) -> int:
    if si.dialect is Shell.POWERSHELL:
        argv = [si.executable, "-NoProfile", "-NonInteractive", "-Command", command_line]
    else:
        argv = ["cmd", "/c", command_line]
    try:
        completed = subprocess.run(argv)
    except FileNotFoundError as e:
        raise RuntimeError(f"executable not found: {argv[0]}") from e
    return completed.returncode