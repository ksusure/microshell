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