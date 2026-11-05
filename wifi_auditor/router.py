"""Module B - the router check.

Two kinds of fact go into this check:

  * MEASURED - what your computer already knows about the network it's on:
    the security mode (WPA2 / WPA3 / mixed), and whether your network *name*
    matches a known default pattern that leaks your router's make/model.

  * DECLARED - the few things only the router knows, which no laptop can read
    over the air: WPS state, management-frame protection (802.11w / PMF),
    firmware currency, whether the admin password was changed, and whether a
    guest network is isolated. You answer these (yes/no/unknown) and we fold
    them in, clearly marked as "you told us".

Honest by design: we never pretend to have measured something we only asked.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Heuristic patterns for ISP / vendor DEFAULT SSIDs (a leak of make/model).
# Not exhaustive; matching one is a nudge, not proof.
_DEFAULT_SSID_PATTERNS = [
    r"NETGEAR\d*", r"Linksys.*", r"TP-?Link[_-].*", r"ATT.{2,}", r"SpectrumSetup-.*",
    r"xfinity.*", r"XFINITY.*", r"Verizon.*", r"FiOS-.*", r"DIRECT-.*", r"HUAWEI-.*",
    r"ASUS.*", r"[dD]link.*", r"belkin\..*", r"[oO]rbi.*", r"CenturyLink.*",
    r"Frontier.*", r"BTHub.*", r"BTWifi.*", r"VM\d{4,}", r"SKY[0-9A-Z]{4,}",
    r"TALKTALK.*", r"VirginMedia.*", r"Telstra.*", r"MyRepublic.*", r"Arris.*",
    r"MOTO.*", r"Netis.*", r"Tenda.*", r"Mercusys.*", r"Globe.*", r"PLDT.*",
]


def classify_auth(auth: str | None) -> str:
    """Return one of: open, wep, wpa, wpa2, mixed, wpa3, unknown."""
    if not auth:
        return "unknown"
    a = auth.lower()
    has2 = "wpa2" in a
    has3 = "wpa3" in a or "sae" in a
    if has2 and has3:
        return "mixed"
    if has3:
        return "wpa3"
    if has2:
        return "wpa2"
    if "wpa" in a:
        return "wpa"
    if "wep" in a:
        return "wep"
    if "open" in a or a in ("none", "80211open"):
        return "open"
    return "unknown"


def is_default_ssid(ssid: str | None) -> bool:
    if not ssid:
        return False
    return any(re.fullmatch(p, ssid) for p in _DEFAULT_SSID_PATTERNS)


@dataclass
class RouterFacts:
    """Declared router facts. None = unknown / not answered."""
    wps_on: bool | None = None
    pmf_on: bool | None = None
    admin_changed: bool | None = None
    firmware_recent: bool | None = None
    guest_isolated: bool | None = None


@dataclass
class Finding:
    key: str
    label: str
    status: str   # good / warn / bad / unknown
    note: str
    measured: bool
    points: int
    max_points: int


@dataclass
class RouterVerdict:
    connected: bool
    ssid: str | None
    auth_class: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def points(self) -> int:
        return sum(f.points for f in self.findings)

    @property
    def max_points(self) -> int:
        return sum(f.max_points for f in self.findings)


def assess(conn: dict | None, facts: RouterFacts) -> RouterVerdict:
    connected = bool(conn and conn.get("connected"))
    ssid = conn.get("ssid") if conn else None
    auth = conn.get("auth") if conn else None
    cls = classify_auth(auth)

    findings: list[Finding] = []

    # --- encryption mode (measured) --------------------------------------
    enc_pts = {"wpa3": 14, "mixed": 9, "wpa2": 7, "wpa": 2,
               "wep": 0, "open": 0, "unknown": 7}[cls]
    enc_status = {"wpa3": "good", "mixed": "warn", "wpa2": "warn", "wpa": "bad",
                  "wep": "bad", "open": "bad", "unknown": "unknown"}[cls]
    enc_note = {
        "wpa3": "WPA3 (SAE) - the strongest home mode; offline guessing doesn't apply.",
        "mixed": "Mixed WPA2/WPA3 - works, but can be downgraded to the WPA2 path. Prefer WPA3-only.",
        "wpa2": "WPA2 - fine with a long passphrase, but WPA3 is stronger if your router offers it.",
        "wpa": "WPA (v1) - outdated and weak. Move to WPA2 or WPA3.",
        "wep": "WEP - broken; anyone nearby can crack it in minutes. Replace the router or mode now.",
        "open": "Open / no encryption - everything is in the clear. Set a WPA2/WPA3 password now.",
        "unknown": "Could not read the security mode on this OS.",
    }[cls]
    findings.append(Finding("encryption", f"Security mode: {auth or 'unknown'}",
                            enc_status, enc_note, measured=True,
                            points=enc_pts, max_points=14))

    # --- default SSID name (measured) ------------------------------------
    default = is_default_ssid(ssid)
    findings.append(Finding(
        "ssid_name", "Network name",
        "warn" if default else "good",
        ("Your network name matches a default pattern - it advertises your router's make/model. Rename it."
         if default else "Your network name doesn't look like a factory default. Good."),
        measured=True, points=0 if default else 4, max_points=4))

    # --- declared facts ---------------------------------------------------
    def declared(key, label, value, good_is_true, pts_good, note_good, note_bad, note_unknown, unknown_pts):
        if value is None:
            return Finding(key, label, "unknown", note_unknown, False, unknown_pts, pts_good)
        ok = (value is good_is_true)
        return Finding(key, label, "good" if ok else "warn",
                       note_good if ok else note_bad, False,
                       pts_good if ok else 0, pts_good)

    findings.append(declared(
        "wps", "WPS (push-button/PIN pairing)", facts.wps_on, False, 6,
        "WPS is off. Good - its PIN has been crackable for over a decade.",
        "WPS is on. Turn it off, and confirm it really turned off.",
        "WPS state unknown - check your router admin page and turn it off.", 3))

    findings.append(declared(
        "pmf", "Management-frame protection (802.11w / PMF)", facts.pmf_on, True, 5,
        "PMF is on - this blunts deauth / knock-off attacks.",
        "PMF is off. Turn it on if your router offers it (WPA3 requires it).",
        "PMF state unknown - check your router; enable it if available.", 2))

    findings.append(declared(
        "admin", "Router admin password", facts.admin_changed, True, 6,
        "Admin password changed from the factory default. Good.",
        "Admin password may still be the sticker default - change it now.",
        "Admin password state unknown - make sure it's not the factory default.", 2))

    findings.append(declared(
        "firmware", "Firmware", facts.firmware_recent, True, 5,
        "Firmware is reasonably current. Good.",
        "Firmware looks old - check for an update; old firmware ships known holes.",
        "Firmware date unknown - check for an update on the admin page.", 2))

    findings.append(declared(
        "guest", "Guest network for IoT", facts.guest_isolated, True, 0,  # scored in nearby/overall as bonus note
        "Smart gadgets are on an isolated guest network. Good.",
        "Put smart plugs/cameras/TVs on a separate, isolated guest network.",
        "Guest-network isolation unknown - consider isolating IoT devices.", 0))

    return RouterVerdict(connected, ssid, cls, findings)
