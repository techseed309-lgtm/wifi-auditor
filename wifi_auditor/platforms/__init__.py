"""Per-OS collectors for the current connection and nearby networks.

Each platform module exposes two functions that return plain dicts/lists (or
None when the data can't be read), so the rest of the tool stays OS-agnostic:

    connection() -> dict | None      # the network this machine is on
    nearby()     -> list[dict]       # networks visible in range (passive)

Nothing here attacks, connects to, or deauthenticates anything. The nearby scan
only lists beacons that are already broadcasting in the open.
"""
from __future__ import annotations

import sys


def _module():
    if sys.platform.startswith("win"):
        from . import windows
        return windows
    if sys.platform.startswith("linux"):
        from . import linux
        return linux
    if sys.platform == "darwin":
        from . import macos
        return macos
    return None


def connection() -> dict | None:
    mod = _module()
    if mod is None:
        return None
    try:
        return mod.connection()
    except Exception:
        return None


def nearby() -> list[dict]:
    mod = _module()
    if mod is None:
        return []
    try:
        return mod.nearby()
    except Exception:
        return []


def platform_name() -> str:
    if sys.platform.startswith("win"):
        return "Windows"
    if sys.platform.startswith("linux"):
        return "Linux"
    if sys.platform == "darwin":
        return "macOS"
    return sys.platform
