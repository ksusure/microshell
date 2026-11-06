from __future__ import annotations

from dataclasses import dataclass, field

from .detector import Shell, ShellInfo, resolve_shell_info
from .mappings.data import CommandMapping
from .parser import CommandList, Pipeline, ParseError, SimpleCommand, parse
from .registry import UnknownCommandError, get_mapping, lookup_flag_group
from .tokenizer import tokenize


class TranslationError(Exception):
    pass


@dataclass
class TranslatedCommand:
    command_line: str
    warnings: list[str] = field(default_factory=list)


_PS_SPECIAL = set(" \t\r\n'\";|&<>()$`")
_CMD_SPECIAL = set(" \t\r\n\"&|<>()^")


def _quote_ps(arg: str) -> str:
    if arg == "":
        return "''"
    if any(ch in _PS_SPECIAL for ch in arg):
        return "'" + arg.replace("'", "''") + "'"
    return arg


def _quote_cmd(arg: str) -> str:
    if arg == "":
        return '""'
    if any(ch in _CMD_SPECIAL for ch in arg):
        return '"' + arg + '"'
    return arg


def _quote(arg: str, dialect: Shell) -> str:
    return _quote_ps(arg) if dialect is Shell.POWERSHELL else _quote_cmd(arg)


# ---------- flag 翻译 ----------

def _apply_one_flag(
    mapping: CommandMapping, flag: str, si: ShellInfo, warnings: list[str]
) -> str | None:
    f = lookup_flag_group(mapping, flag)
    if f is None:
        return None
    frag = f.powershell if si.dialect is Shell.POWERSHELL else f.cmd
    if frag:
        return frag
    lossy = f.ps_lossy if si.dialect is Shell.POWERSHELL else f.cmd_lossy
    if lossy:
        warnings.append(
            f"flag {flag} for '{mapping.unix}' has no equivalent in {si.dialect.value}; dropped"
        )
    return ""


def _translate_flags(
    mapping: CommandMapping, flags: list[str], si: ShellInfo, warnings: list[str]
) -> list[str]:
    out: list[str] = []
    for flag in flags:
        frag = _apply_one_flag(mapping, flag, si, warnings)
        if frag:
            out.append(frag)
            continue
        if frag is not None:
            continue
        body = flag[1:]
        if len(body) > 1:
            subs = ["-" + ch for ch in body]
            if all(lookup_flag_group(mapping, s) is not None for s in subs):
                for s in subs:
                    sub_frag = _apply_one_flag(mapping, s, si, warnings)
                    if sub_frag:
                        out.append(sub_frag)
                continue
        warnings.append(f"flag {flag} for '{mapping.unix}' is unknown; dropped")
    return out


# ---------- 位置参数映射 ----------

def _apply_positional_map(
    mapping: CommandMapping, args: list[str], si: ShellInfo
) -> list[str]:
    if not args:
        return []
    pm = mapping.positional_map
    if not pm:
        return [_quote(a, si.dialect) for a in args]

    result: list[str] = []
    i = 0
    for j, key in enumerate(pm):
        if j == len(pm) - 1:
            remaining = args[i:]
            if remaining:
                quoted = [_quote(a, si.dialect) for a in remaining]
                if len(quoted) == 1:
                    result.extend([f"-{key}", quoted[0]])
                else:
                    result.extend([f"-{key}", ", ".join(quoted)])
            i = len(args)
        else:
            if i < len(args):
                result.extend([f"-{key}", _quote(args[i], si.dialect)])
                i += 1
    if i < len(args):
        result.extend(_quote(a, si.dialect) for a in args[i:])
    return result


# ---------- 简单命令翻译 ----------

def _translate_simple(cmd: SimpleCommand, si: ShellInfo, warnings: list[str]) -> str:
    mapping = get_mapping(cmd.name)

    if si.dialect is Shell.POWERSHELL and mapping.powershell is None:
        raise TranslationError(f"'{cmd.name}' has no PowerShell equivalent")
    if si.dialect is Shell.CMD and mapping.cmd is None:
        raise TranslationError(f"'{cmd.name}' has no CMD equivalent")

    for r in cmd.redirects:
        if r.op == "<":
            raise TranslationError(
                "input redirection '<' is not supported; use a pipe instead"
            )

    flags: list[str] = []
    args: list[str] = []
    seen_ddash = False
    for w in cmd.words:
        if not seen_ddash and w == "--":
            seen_ddash = True
            continue
        if not seen_ddash and w.startswith("-") and w != "-":
            flags.append(w)
        else:
            args.append(w)

    translated_flags = _translate_flags(mapping, flags, si, warnings)

    if si.dialect is Shell.POWERSHELL:
        head = mapping.powershell
        parts: list[str] = [head, *mapping.ps_extra, *translated_flags]
    else:
        head = mapping.cmd
        parts = [head, *mapping.cmd_extra, *translated_flags]

    parts.extend(_apply_positional_map(mapping, args, si))

    for r in cmd.redirects:
        if r.op == "2>&1":
            parts.append("2>&1")
        else:
            parts.append(f"{r.op} {_quote(r.target, si.dialect)}")

    return " ".join(parts)


# ---------- 管道与连接符 ----------

def _translate_pipeline(pl: Pipeline, si: ShellInfo, warnings: list[str]) -> str:
    return " | ".join(_translate_simple(s, si, warnings) for s in pl.stages)


def _apply_connector(first: str, op: str, rest: str, si: ShellInfo) -> str:
    if op == ";":
        if si.dialect is Shell.POWERSHELL:
            return f"{first}; {rest}"
        return f"{first} & {rest}"

    if op == "&&":
        if si.dialect is Shell.POWERSHELL and not si.supports_and_or:
            return f"{first}; if ($?) {{ {rest} }}"
        return f"{first} && {rest}"

    if op == "||":
        if si.dialect is Shell.POWERSHELL and not si.supports_and_or:
            return f"{first}; if (-not $?) {{ {rest} }}"
        return f"{first} || {rest}"

    raise TranslationError(f"unsupported connector '{op}'")


def _translate_command_list(cl: CommandList, si: ShellInfo, warnings: list[str]) -> str:
    def rec(idx: int) -> str:
        if idx == len(cl.items) - 1:
            return _translate_pipeline(cl.items[idx], si, warnings)
        first = _translate_pipeline(cl.items[idx], si, warnings)
        op = cl.connectors[idx]
        rest = rec(idx + 1)
        return _apply_connector(first, op, rest, si)

    return rec(0)


# ---------- 顶层 API ----------

def _to_shell_info(shell: Shell | ShellInfo) -> ShellInfo:
    if isinstance(shell, ShellInfo):
        return shell
    if shell is Shell.POWERSHELL:
        return ShellInfo(Shell.POWERSHELL, 7, 0)
    return ShellInfo(Shell.CMD, 10, 0)


def translate(line: str, shell: Shell | ShellInfo) -> TranslatedCommand:
    si = _to_shell_info(shell)
    tokens = tokenize(line)
    ast = parse(tokens)
    warnings: list[str] = []
    command_line = _translate_command_list(ast, si, warnings)
    return TranslatedCommand(command_line, warnings)