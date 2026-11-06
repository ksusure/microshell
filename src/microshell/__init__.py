from .detector import Shell, ShellInfo, resolve_shell, resolve_shell_info
from .parser import ParseError
from .translator import translate, TranslationError, TranslatedCommand
from .registry import UnknownCommandError

__all__ = [
    "Shell", "ShellInfo", "resolve_shell", "resolve_shell_info",
    "translate", "TranslationError", "TranslatedCommand",
    "UnknownCommandError", "ParseError",
]