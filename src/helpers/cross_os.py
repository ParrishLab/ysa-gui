import sys
from typing import Any


def get_os_specific(mac: Any, win32b: Any, win64b: Any = None) -> Any:
    """
    Returns the appropriate value based on the operating system.

    Parameters:
        mac: Value for macOS
        win32b: Value for 32-bit Windows
        win64b: Value for 64-bit Windows
    """
    if sys.platform == "darwin":
        return mac
    elif sys.platform == "win32":
        if sys.maxsize > 2**32:
            return win64b if win64b is not None else win32b
        else:
            return win32b
    else:
        raise ValueError(f"Unsupported operating system: {sys.platform}")
