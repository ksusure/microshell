import pytest

from microshell.parser import ParseError, parse
from microshell.tokenizer import tokenize


def _ast(line):
    return parse(tokenize(line))


def test_simple():
    cl = _ast("ls -la /tmp")
    assert len(cl.items) == 1
    assert len(cl.items[0].stages) == 1
    assert cl.items[0].stages[0].name == "ls"
    assert cl.items[0].stages[0].words == ["-la", "/tmp"]
    assert cl.connectors == []


def test_pipeline():
    cl = _ast("ls | grep foo")
    assert len(cl.items) == 1
    assert len(cl.items[0].stages) == 2
    assert cl.items[0].stages[0].name == "ls"
    assert cl.items[0].stages[1].name == "grep"


def test_connectors():
    cl = _ast("a && b ; c || d")
    assert [p.stages[0].name for p in cl.items] == ["a", "b", "c", "d"]
    assert cl.connectors == ["&&", ";", "||"]


def test_redirect():
    cl = _ast("ls > out.txt")
    sc = cl.items[0].stages[0]
    assert len(sc.redirects) == 1
    assert sc.redirects[0].op == ">"
    assert sc.redirects[0].target == "out.txt"


def test_redirect_needs_target():
    with pytest.raises(ParseError):
        _ast("ls >")


def test_unexpected_leading_connector():
    with pytest.raises(ParseError):
        _ast("&& ls")