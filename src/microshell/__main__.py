from __future__ import annotations

import argparse
import sys

from .detector import resolve_shell_info
from .executor import execute
from .parser import ParseError
from .registry import UnknownCommandError
from .translator import TranslationError, translate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="microshell",
        description="Translate a subset of Unix commands to PowerShell/CMD and run them.",
    )
    parser.add_argument("command", nargs="+", help="Unix-style command line")
    parser.add_argument(
        "--shell", default=None,
        choices=["pwsh", "powershell", "cmd"],
        help="target shell dialect (default: powershell 5.1)",
    )
    parser.add_argument("--dry-run", action="store_true", help="print translation only")
    parser.add_argument("--lint", action="store_true", help="print translation + warnings only")
    args = parser.parse_args(argv)

    line = " ".join(args.command)
    try:
        si = resolve_shell_info(args.shell)
    except ValueError as e:
        print(f"microshell: {e}", file=sys.stderr)
        return 2

    try:
        result = translate(line, si)
    except UnknownCommandError as e:
        print(f"microshell: unsupported command '{e.args[0]}'", file=sys.stderr)
        return 127
    except (TranslationError, ParseError) as e:
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

    return execute(result.command_line, si)


if __name__ == "__main__":
    raise SystemExit(main())