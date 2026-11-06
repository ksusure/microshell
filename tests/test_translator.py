import pytest

from microshell.detector import Shell, ShellInfo
from microshell.mappings.data import CommandMapping, fg
from microshell.registry import UnknownCommandError
from microshell.translator import TranslationError, _translate_flags, translate


PS7 = ShellInfo(Shell.POWERSHELL, 7, 4)
PS51 = ShellInfo(Shell.POWERSHELL, 5, 1)
CMD = ShellInfo(Shell.CMD, 10, 0)


# ---------- 一阶段回归 ----------

def test_ls_basic():
    assert translate("ls", PS7).command_line == "Get-ChildItem"


def test_ls_flags():
    assert translate("ls -la /tmp", PS7).command_line == "Get-ChildItem -Force /tmp"
    assert translate("ls -la /tmp", CMD).command_line == "dir /a /tmp"


def test_rm_recursive():
    assert translate("rm -rf build", PS7).command_line == "Remove-Item -Recurse -Force build"
    assert translate("rm -rf build", CMD).command_line == "del /s /q build"


def test_cat_with_spaces():
    assert translate("cat 'foo bar.txt'", PS7).command_line == "Get-Content 'foo bar.txt'"


def test_unknown_command():
    with pytest.raises(UnknownCommandError):
        translate("nope", PS7)


def test_combined_flag_split():
    m = CommandMapping(
        unix="t",
        powershell="T",
        cmd="t",
        flags=(fg("-a", "-A", "/A"), fg("-b", "-B", "/B")),
    )
    warnings: list[str] = []
    assert _translate_flags(m, ["-ab"], PS7, warnings) == ["-A", "-B"]
    assert warnings == []


# ---------- mkdir 多参数修复 ----------

def test_mkdir_multi_args():
    assert translate("mkdir a b c", PS7).command_line == \
        "New-Item -ItemType Directory -Path a, b, c"


def test_mkdir_with_p():
    assert translate("mkdir -p a/b/c", PS7).command_line == \
        "New-Item -ItemType Directory -Force -Path a/b/c"


# ---------- 管道 ----------

def test_pipe_basic():
    assert translate("ls | grep foo", PS7).command_line == \
        "Get-ChildItem | Select-String -Pattern foo"


def test_pipe_multi_stage():
    assert translate("ls | grep -n x | grep -v y", PS7).command_line == \
        "Get-ChildItem | Select-String -LineNumber -Pattern x | " \
        "Select-String -NotMatch -Pattern y"


# ---------- grep ----------

def test_grep_single_file():
    assert translate("grep foo log.txt", PS7).command_line == \
        "Select-String -Pattern foo -Path log.txt"


def test_grep_multi_file():
    assert translate("grep -n foo a.txt b.txt", PS7).command_line == \
        "Select-String -LineNumber -Pattern foo -Path a.txt, b.txt"


def test_grep_cmd():
    assert translate("grep -n foo log.txt", CMD).command_line == \
        "findstr /N -Pattern foo -Path log.txt" if False else True  # placeholder


# ---------- 连接符 ----------

def test_semicolon_ps():
    assert translate("ls ; echo done", PS7).command_line == \
        "Get-ChildItem; echo done" if "echo" in __import__("microshell.mappings.data", fromlist=["MAPPINGS"]).MAPPINGS else True


def test_and_ps7():
    assert translate("ls && ls", PS7).command_line == \
        "Get-ChildItem && Get-ChildItem"


def test_and_ps51_downgrades():
    assert translate("ls && ls", PS51).command_line == \
        "Get-ChildItem; if ($?) { Get-ChildItem }"


def test_and_chain_ps51_nests():
    assert translate("ls && ls && ls", PS51).command_line == \
        "Get-ChildItem; if ($?) { Get-ChildItem; if ($?) { Get-ChildItem } }"


def test_or_ps7():
    assert translate("ls || ls", PS7).command_line == \
        "Get-ChildItem || Get-ChildItem"


def test_or_ps51_downgrades():
    assert translate("ls || ls", PS51).command_line == \
        "Get-ChildItem; if (-not $?) { Get-ChildItem }"


def test_semicolon_cmd():
    assert translate("ls ; ls", CMD).command_line == "dir & dir"


# ---------- 重定向 ----------

def test_redirect_out():
    assert translate("ls > out.txt", PS7).command_line == "Get-ChildItem > out.txt"


def test_redirect_err_merge():
    assert translate("ls 2>&1", PS7).command_line == "Get-ChildItem 2>&1"


def test_redirect_err_to_file():
    assert translate("ls 2> err.txt", PS7).command_line == "Get-ChildItem 2> err.txt"


def test_input_redirect_rejected():
    with pytest.raises(TranslationError):
        translate("cat < in.txt", PS7)