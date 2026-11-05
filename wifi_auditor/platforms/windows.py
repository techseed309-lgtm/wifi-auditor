"""Windows collectors via netsh (English output assumed).

    netsh wlan show interfaces        -> the connection we're on
    netsh wlan show networks mode=bssid -> networks in range (passive list)
"""
from __future__ import annotations

import re
import subprocess


def _run(args: list[str]) -> str:
    try:
        return subprocess.run(
            args, capture_output=True, text=True, timeout=30
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _grab(label: str, text: str) -> str | None:
    # Anchor at start-of-line so "SSID" doesn't match "BSSID".
    m = re.search(rf"^\s*{re.escape(label)}\s*:\s*(.+?)\s*$", text, re.MULTILINE)
    return m.group(1) if m else None


def connection() -> dict | None:
    out = _run(["netsh", "wlan", "show", "interfaces"])
    if not out or "There is no wireless interface" in out:
        return None
    state = _grab("State", out)
    if state and state.lower() != "connected":
        return {"connected": False, "state": state}
    return {
        "connected": True,
        "ssid": _grab("SSID", out),
        "bssid": _grab("BSSID", out),
        "auth": _grab("Authentication", out),
        "cipher": _grab("Cipher", out),
        "radio": _grab("Radio type", out),
        "band": _grab("Band", out),
        "signal": _grab("Signal", out),
    }


def nearby() -> list[dict]:
    out = _run(["netsh", "wlan", "show", "networks", "mode=bssid"])
    if not out:
        return []
    nets: list[dict] = []
    # Blocks start with "SSID 1 : <name>" ... each may contain Authentication and BSSIDs.
    blocks = re.split(r"\n(?=SSID \d+ :)", out)
    for b in blocks:
        m = re.match(r"SSID \d+ :\s*(.*?)\s*\n", b)
        if not m:
            continue
        ssid = m.group(1)  # may be empty for hidden networks
        auth = _grab("Authentication", b)
        bssids = re.findall(r"^\s*BSSID \d+\s*:\s*([0-9a-fA-F:]{17})", b, re.MULTILINE)
        nets.append({"ssid": ssid, "auth": auth, "bssids": bssids,
                     "bssid_count": len(bssids)})
    return nets
