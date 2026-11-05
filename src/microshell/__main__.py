from __future__ import annotations

import argparse
import sys

from .detector import resolve_shell
from .executor import execute
from .registry import UnknownCommandError
from .translator import TranslationError, translate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="microshell",
        description="Translate a subset of Unix commands to PowerShell/CMD and run them.",
    )
    parser.add_argument("command", nargs="+", help="Unix-style command line")
    parser.add_argument("--shell", default=None, choices=["powershell", "pwsh", "cmd"])
    parser.add_argument("--dry-run", action="store_true", help="print translation only")
    parser.add_argument("--lint", action="store_true", help="print translation + warnings only")
    args = parser.parse_args(argv)

    line = " ".join(args.command)
    shell = resolve_shell(args.shell)

    try:
        result = translate(line, shell)
    except UnknownCommandError as e:
        print(f"microshell: unsupported command '{e.args[0]}'", file=sys.stderr)
        return 127
    except TranslationError as e:
        print(f"microshell: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"microshell: {e}", file=sys.stderr)
        return 2

    for w in result.warnings:
        print(f"microshell: warning: {w}", file=sys.stderr)

    if args.dry_run or args.lint:
        print(result.command_line)
        return 0

    return execute(result.command_line, shell)


if __name__ == "__main__":
    raise SystemExit(main())