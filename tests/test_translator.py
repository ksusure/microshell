import pytest

from microshell.detector import Shell
from microshell.mappings.data import CommandMapping, fg
from microshell.registry import UnknownCommandError
from microshell.translator import TranslationError, _translate_flags, translate


PS = Shell.POWERSHELL
CMD = Shell.CMD


def test_ls_basic():
    assert translate("ls", PS).command_line == "Get-ChildItem"


def test_ls_flags():
    assert translate("ls -la /tmp", PS).command_line == "Get-ChildItem -Force /tmp"
    assert translate("ls -la /tmp", CMD).command_line == "dir /a /tmp"


def test_rm_recursive():
    assert translate("rm -rf build", PS).command_line == "Remove-Item -Recurse -Force build"
    assert translate("rm -rf build", CMD).command_line == "del /s /q build"


def test_mkdir_extra_args():
    assert translate("mkdir -p a b", PS).command_line == \
        "New-Item -ItemType Directory -Force a b"


def test_cat_with_spaces():
    assert translate("cat 'foo bar.txt'", PS).command_line == "Get-Content 'foo bar.txt'"


def test_unknown_command():
    with pytest.raises(UnknownCommandError):
        translate("nope", PS)


def test_pipe_rejected_in_phase1():
    with pytest.raises(TranslationError):
        translate("ls | grep x", PS)


def test_lossy_flag_warns():
    r = translate("cp -r src dst", CMD)
    assert r.command_line == "copy src dst"
    assert any("cp" in w and "-r" in w for w in r.warnings)


def test_combined_flag_split():
    m = CommandMapping(
        unix="t",
        powershell="T",
        cmd="t",
        flags=(fg("-a", "-A", "/A"), fg("-b", "-B", "/B")),
    )
    warnings: list[str] = []
    assert _translate_flags(m, ["-ab"], PS, warnings) == ["-A", "-B"]
    assert warnings == []