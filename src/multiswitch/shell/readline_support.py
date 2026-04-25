from typing import Any, Tuple


def get_readline_module() -> Tuple[Any, bool]:
    try:
        import readline  # type: ignore
        return readline, True
    except Exception:
        pass

    try:
        import pyreadline3 as readline  # type: ignore
        return readline, True
    except Exception:
        return None, False
