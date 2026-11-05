from __future__ import annotations

from .mappings.data import MAPPINGS, CommandMapping, FlagGroup


class UnknownCommandError(Exception):
    pass


def get_mapping(name: str) -> CommandMapping:
    try:
        return MAPPINGS[name]
    except KeyError:
        raise UnknownCommandError(name) from None


def lookup_flag_group(mapping: CommandMapping, unix_flag: str) -> FlagGroup | None:
    for f in mapping.flags:
        if f.unix == unix_flag:
            return f
    return None