"""Linux collectors via nmcli (NetworkManager). Best-effort."""
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
    # Active Wi-Fi line, terminal-mode (-t) colon-separated fields.
    out = _run(["nmcli", "-t", "-f", "ACTIVE,SSID,BSSID,SECURITY,CHAN,SIGNAL",
                "dev", "wifi"])
    if not out:
        return None
    for line in out.splitlines():
        # nmcli escapes ':' in BSSIDs as '\:', so split carefully.
        parts = line.replace("\\:", "\0").split(":")
        parts = [p.replace("\0", ":") for p in parts]
        if parts and parts[0] == "yes":
            active, ssid, bssid, security, chan, signal = (parts + [None] * 6)[:6]
            return {
                "connected": True,
                "ssid": ssid or None,
                "bssid": bssid or None,
                "auth": security or None,   # e.g. "WPA2", "WPA3", "WPA2 WPA3"
                "cipher": None,
                "radio": None,
                "band": None,
                "signal": signal,
            }
    return {"connected": False, "state": "not connected"}


def nearby() -> list[dict]:
    out = _run(["nmcli", "-t", "-f", "SSID,BSSID,SECURITY", "dev", "wifi"])
    if not out:
        return []
    by_ssid: dict[str, dict] = {}
    for line in out.splitlines():
        parts = line.replace("\\:", "\0").split(":")
        parts = [p.replace("\0", ":") for p in parts]
        if len(parts) < 2:
            continue
        ssid = parts[0]
        bssid = parts[1]
        auth = parts[2] if len(parts) > 2 else None
        rec = by_ssid.setdefault(ssid, {"ssid": ssid, "auth": auth, "bssids": []})
        if bssid:
            rec["bssids"].append(bssid)
    nets = []
    for rec in by_ssid.values():
        rec["bssid_count"] = len(rec["bssids"])
        nets.append(rec)
    return nets
