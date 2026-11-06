from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FlagGroup:
    unix: str
    powershell: str
    cmd: str
    ps_lossy: bool = False
    cmd_lossy: bool = False


@dataclass(frozen=True)
class CommandMapping:
    unix: str
    powershell: str | None
    cmd: str | None
    flags: tuple[FlagGroup, ...] = ()
    ps_extra: tuple[str, ...] = ()
    cmd_extra: tuple[str, ...] = ()
    positional_map: tuple[str, ...] = ()   # 空 = 位置参数按原样拼接


def fg(unix: str, ps: str, cmd: str, *, ps_lossy: bool = False, cmd_lossy: bool = False) -> FlagGroup:
    return FlagGroup(unix, ps, cmd, ps_lossy, cmd_lossy)


MAPPINGS: dict[str, CommandMapping] = {}


def _register(m: CommandMapping) -> None:
    MAPPINGS[m.unix] = m


_register(CommandMapping(
    unix="ls",
    powershell="Get-ChildItem",
    cmd="dir",
    flags=(
        fg("-l", "", ""),
        fg("-a", "-Force", "/a"),
        fg("-la", "-Force", "/a"),
        fg("-al", "-Force", "/a"),
        fg("-h", "", ""),
    ),
))

_register(CommandMapping(
    unix="rm",
    powershell="Remove-Item",
    cmd="del",
    flags=(
        fg("-r", "-Recurse", "/s"),
        fg("-f", "-Force", "/q"),
        fg("-rf", "-Recurse -Force", "/s /q"),
        fg("-fr", "-Recurse -Force", "/s /q"),
    ),
))

_register(CommandMapping(
    unix="cp",
    powershell="Copy-Item",
    cmd="copy",
    flags=(
        fg("-r", "-Recurse", "", cmd_lossy=True),
        fg("-f", "-Force", ""),
        fg("-rf", "-Recurse -Force", "", cmd_lossy=True),
    ),
))

_register(CommandMapping(
    unix="mv",
    powershell="Move-Item",
    cmd="move",
    flags=(fg("-f", "-Force", ""),),
))

_register(CommandMapping(
    unix="cat",
    powershell="Get-Content",
    cmd="type",
))

_register(CommandMapping(
    unix="mkdir",
    powershell="New-Item",
    cmd="mkdir",
    ps_extra=("-ItemType", "Directory"),
    positional_map=("Path",),       # 所有位置参数都用 -Path 打包
    flags=(fg("-p", "-Force", ""),),
))

_register(CommandMapping(
    unix="grep",
    powershell="Select-String",
    cmd="findstr",
    positional_map=("Pattern", "Path"),   # 第一个位置是 Pattern，其余全部进 Path
    flags=(
        fg("-i", "", "/I"),                # Select-String 默认大小写不敏感
        fg("-n", "-LineNumber", "/N"),
        fg("-v", "-NotMatch", "/V"),
        fg("-r", "", "", ps_lossy=True, cmd_lossy=True),
    ),
))