from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FlagGroup:
    unix: str
    powershell: str
    cmd: str
    ps_lossy: bool = False   # 空翻译且为 True 时警告
    cmd_lossy: bool = False


@dataclass(frozen=True)
class CommandMapping:
    unix: str
    powershell: str
    cmd: str
    flags: tuple[FlagGroup, ...] = ()
    ps_extra: tuple[str, ...] = ()   # 命令名之后追加的固定参数
    cmd_extra: tuple[str, ...] = ()


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
        fg("-l", "", ""),            # Get-ChildItem 默认即列表格式
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
    flags=(fg("-p", "-Force", ""),),   # CMD 的 mkdir 默认创建中间目录
))