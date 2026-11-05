"""macOS collectors via system_profiler. Best-effort.

Recent macOS hides live scan details behind `wdutil info` (needs sudo) and has
deprecated the old `airport` tool. We read what system_profiler exposes without
elevation; fields that aren't available come back as None and the report says so.
"""
from __future__ import annotations

import subprocess


def _run(args: list[str]) -> str:
    try:
        return subprocess.run(
            args, capture_output=True, text=True, timeout=30
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def connection() -> dict | None:
    out = _run(["system_profiler", "SPAirPortDataType"])
    if not out:
        return None
    # Find the "Current Network Information:" block and read the first entries.
    lines = out.splitlines()
    ssid = auth = None
    for i, line in enumerate(lines):
        if "Current Network Information:" in line:
            # The next non-empty indented line is the SSID (ends with ':').
            for j in range(i + 1, min(i + 15, len(lines))):
                s = lines[j].strip()
                if s and s.endswith(":") and ssid is None:
                    ssid = s[:-1]
                if s.lower().startswith("security:"):
                    auth = s.split(":", 1)[1].strip()
            break
    if ssid is None and auth is None:
        return {"connected": False, "state": "could not read (try: sudo wdutil info)"}
    return {
        "connected": True,
        "ssid": ssid,
        "bssid": None,
        "auth": auth,       # e.g. "WPA2 Personal", "WPA3 Personal"
        "cipher": None,
        "radio": None,
        "band": None,
        "signal": None,
    }


def nearby() -> list[dict]:
    # Modern macOS restricts unelevated scans; return empty and let the report
    # explain rather than guess.
    return []
