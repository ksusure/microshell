from __future__ import annotations

from dataclasses import dataclass, field

from .detector import Shell
from .mappings.data import CommandMapping
from .registry import UnknownCommandError, get_mapping, lookup_flag_group
from .tokenizer import Token, TokenType, tokenize


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


def _quote(arg: str, shell: Shell) -> str:
    return _quote_ps(arg) if shell is Shell.POWERSHELL else _quote_cmd(arg)


def _split_flags(tokens: list[Token]) -> tuple[list[str], list[str]]:
    flags: list[str] = []
    args: list[str] = []
    seen_ddash = False
    for t in tokens:
        if t.type is not TokenType.WORD:
            raise TranslationError(
                f"unsupported token '{t.value}' ({t.type.name}); "
                f"connectors/pipes/redirects are not supported in phase 1"
            )
        if not seen_ddash and t.value == "--":
            seen_ddash = True
            continue
        if not seen_ddash and t.value.startswith("-") and t.value != "-":
            flags.append(t.value)
        else:
            args.append(t.value)
    return flags, args


def _apply_one_flag(
    mapping: CommandMapping, flag: str, shell: Shell, warnings: list[str]
) -> str | None:
    """返回翻译片段；'' 表示安全处理但无输出；None 表示无法处理（已警告）。"""
    f = lookup_flag_group(mapping, flag)
    if f is None:
        return None
    frag = f.powershell if shell is Shell.POWERSHELL else f.cmd
    if frag:
        return frag
    lossy = f.ps_lossy if shell is Shell.POWERSHELL else f.cmd_lossy
    if lossy:
        warnings.append(
            f"flag {flag} for '{mapping.unix}' has no equivalent in {shell.value}; dropped"
        )
    return ""


def _translate_flags(
    mapping: CommandMapping, flags: list[str], shell: Shell, warnings: list[str]
) -> list[str]:
    out: list[str] = []
    for flag in flags:
        frag = _apply_one_flag(mapping, flag, shell, warnings)
        if frag:
            out.append(frag)
            continue
        if frag is not None:
            continue
        # 组合拆分：-abc → -a -b -c，仅当每个单字符 flag 都已登记时采用
        body = flag[1:]
        if len(body) > 1:
            subs = ["-" + ch for ch in body]
            if all(lookup_flag_group(mapping, s) is not None for s in subs):
                for s in subs:
                    sub_frag = _apply_one_flag(mapping, s, shell, warnings)
                    if sub_frag:
                        out.append(sub_frag)
                continue
        warnings.append(f"flag {flag} for '{mapping.unix}' is unknown; dropped")
    return out


def translate(line: str, shell: Shell) -> TranslatedCommand:
    tokens = tokenize(line)
    if not tokens:
        raise TranslationError("empty command")

    head = tokens[0]
    if head.type is not TokenType.WORD:
        raise TranslationError(f"expected command name, got '{head.value}'")

    try:
        mapping = get_mapping(head.value)
    except UnknownCommandError:
        raise

    flags, args = _split_flags(tokens[1:])
    warnings: list[str] = []
    translated_flags = _translate_flags(mapping, flags, shell, warnings)

    if shell is Shell.POWERSHELL:
        parts = [mapping.powershell, *mapping.ps_extra, *translated_flags]
    else:
        parts = [mapping.cmd, *mapping.cmd_extra, *translated_flags]

    for a in args:
        if shell is Shell.CMD and '"' in a:
            warnings.append(f"argument contains double quote; CMD quoting is unreliable: {a!r}")
        parts.append(_quote(a, shell))

    return TranslatedCommand(" ".join(parts), warnings)