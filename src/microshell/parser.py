from __future__ import annotations

from dataclasses import dataclass, field

from .tokenizer import Token, TokenType


class ParseError(Exception):
    pass


@dataclass
class Redirect:
    fd: int
    op: str
    target: str | None    # None 仅用于 2>&1


@dataclass
class SimpleCommand:
    name: str
    words: list[str]
    redirects: list[Redirect] = field(default_factory=list)


@dataclass
class Pipeline:
    stages: list[SimpleCommand]


@dataclass
class CommandList:
    items: list[Pipeline]
    connectors: list[str]


def parse(tokens: list[Token]) -> CommandList:
    if not tokens:
        raise ParseError("empty command")
    items: list[Pipeline] = []
    connectors: list[str] = []
    current: list[Token] = []
    for t in tokens:
        if t.type in (TokenType.AND, TokenType.OR, TokenType.SEMI):
            if not current:
                raise ParseError(f"unexpected connector '{t.value}'")
            items.append(_parse_pipeline(current))
            connectors.append(t.value)
            current = []
        else:
            current.append(t)
    if not current:
        raise ParseError("trailing connector")
    items.append(_parse_pipeline(current))
    return CommandList(items, connectors)


def _parse_pipeline(tokens: list[Token]) -> Pipeline:
    stages: list[SimpleCommand] = []
    current: list[Token] = []
    for t in tokens:
        if t.type is TokenType.PIPE:
            if not current:
                raise ParseError("empty pipeline stage")
            stages.append(_parse_simple(current))
            current = []
        else:
            current.append(t)
    if not current:
        raise ParseError("empty pipeline stage")
    stages.append(_parse_simple(current))
    return Pipeline(stages)


def _parse_simple(tokens: list[Token]) -> SimpleCommand:
    words: list[str] = []
    redirects: list[Redirect] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.type is TokenType.WORD:
            words.append(t.value)
            i += 1
        elif t.type is TokenType.REDIRECT:
            if t.value == "2>&1":
                redirects.append(Redirect(2, "2>&1", None))
                i += 1
            else:
                if i + 1 >= len(tokens) or tokens[i + 1].type is not TokenType.WORD:
                    raise ParseError(f"redirection '{t.value}' requires a target")
                if t.value in (">", ">>"):
                    fd = 1
                elif t.value in ("2>", "2>>"):
                    fd = 2
                elif t.value == "<":
                    fd = 0
                else:
                    raise ParseError(f"unsupported redirection '{t.value}'")
                redirects.append(Redirect(fd, t.value, tokens[i + 1].value))
                i += 2
        else:
            raise ParseError(f"unexpected token '{t.value}'")
    if not words:
        raise ParseError("empty command")
    return SimpleCommand(words[0], words[1:], redirects)