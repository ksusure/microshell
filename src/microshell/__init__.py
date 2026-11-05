from .detector import Shell, resolve_shell
from .translator import translate, TranslationError, TranslatedCommand
from .registry import UnknownCommandError

__all__ = [
    "Shell", "resolve_shell",
    "translate", "TranslationError", "TranslatedCommand",
    "UnknownCommandError",
]