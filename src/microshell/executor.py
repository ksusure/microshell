from __future__ import annotations

import subprocess

from .detector import Shell


def execute(command_line: str, shell: Shell) -> int:
    if shell is Shell.POWERSHELL:
        argv = ["powershell", "-NoProfile", "-NonInteractive", "-Command", command_line]
    else:
        argv = ["cmd", "/c", command_line]
    completed = subprocess.run(argv)
    return completed.returncode