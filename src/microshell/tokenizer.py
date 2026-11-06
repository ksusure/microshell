from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    WORD = auto()
    PIPE = auto()
    AND = auto()
    OR = auto()
    SEMI = auto()
    REDIRECT = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str


# 长操作符在前，避免 ">>" 被 ">" 抢先匹配，避免 "2>&1" 被 "2>" 抢先匹配
_OPERATORS: tuple[tuple[str, TokenType], ...] = (
    ("2>&1", TokenType.REDIRECT),
    ("2>>", TokenType.REDIRECT),
    ("2>", TokenType.REDIRECT),
    ("&&", TokenType.AND),
    ("||", TokenType.OR),
    (">>", TokenType.REDIRECT),
    (">", TokenType.REDIRECT),
    ("<", TokenType.REDIRECT),
    ("|", TokenType.PIPE),
    (";", TokenType.SEMI),
)


def tokenize(line: str) -> list[Token]:
    tokens: list[Token] = []
    buf: list[str] = []
    i, n = 0, len(line)

    def flush() -> None:
        if buf:
            tokens.append(Token(TokenType.WORD, "".join(buf)))
            buf.clear()

    while i < n:
        ch = line[i]

        if ch in " \t\r\n":
            flush()
            i += 1
            continue

        if ch == "'":
            i += 1
            while i < n and line[i] != "'":
                buf.append(line[i])
                i += 1
            if i >= n:
                raise ValueError("unterminated single quote")
            i += 1
            continue

        if ch == '"':
            i += 1
            while i < n and line[i] != '"':
                if line[i] == "\\" and i + 1 < n and line[i + 1] in '"\\$`':
                    buf.append(line[i + 1])
                    i += 2
                    continue
                buf.append(line[i])
                i += 1
            if i >= n:
                raise ValueError("unterminated double quote")
            i += 1
            continue

        if ch == "\\" and i + 1 < n:
            buf.append(line[i + 1])
            i += 2
            continue

        matched = False
        for op, ttype in _OPERATORS:
            if line.startswith(op, i):
                flush()
                tokens.append(Token(ttype, op))
                i += len(op)
                matched = True
                break
        if matched:
            continue

        buf.append(ch)
        i += 1

    flush()
    return tokens