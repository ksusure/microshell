import pytest

from microshell.tokenizer import TokenType, tokenize


def test_words_and_flags():
    ts = tokenize("ls -la /tmp")
    assert [t.value for t in ts] == ["ls", "-la", "/tmp"]
    assert all(t.type is TokenType.WORD for t in ts)


def test_single_quotes_preserve_spaces():
    ts = tokenize("cat 'foo bar.txt'")
    assert [t.value for t in ts] == ["cat", "foo bar.txt"]


def test_double_quotes_escape():
    ts = tokenize(r'cat "a\"b"')
    assert [t.value for t in ts] == ["cat", 'a"b']


def test_operators():
    ts = tokenize("ls | grep x && echo ok")
    types = [t.type for t in ts]
    assert TokenType.PIPE in types
    assert TokenType.AND in types


def test_unterminated_quote():
    with pytest.raises(ValueError):
        tokenize("cat 'abc")


def test_stderr_redirect():
    ts = tokenize("ls 2> err.txt")
    assert [t.value for t in ts] == ["ls", "2>", "err.txt"]
    assert ts[1].type is TokenType.REDIRECT


def test_stderr_merge():
    ts = tokenize("ls 2>&1")
    assert [t.value for t in ts] == ["ls", "2>&1"]
    assert ts[1].type is TokenType.REDIRECT