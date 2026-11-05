"""Module D - the report card.

Combines the password verdict (A), router check (B) and neighbourhood check (C)
into a 0-100 score, a letter grade, and a ranked, do-it-tonight fix list.
Also renders the whole thing as plain text for the CLI and the GUI.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .passphrase import PassphraseVerdict
from .router import RouterVerdict
from .nearby import NearbyVerdict

_STATUS_TAG = {"good": "[OK]", "warn": "[! ]", "bad": "[X ]", "unknown": "[? ]"}


@dataclass
class Fix:
    priority: int
    text: str


@dataclass
class Report:
    platform: str
    pp: PassphraseVerdict
    rv: RouterVerdict
    nv: NearbyVerdict
    score: int
    grade: str
    capped: bool
    fixes: list[Fix] = field(default_factory=list)


def _letter(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _build_fixes(pp: PassphraseVerdict, rv: RouterVerdict, nv: NearbyVerdict) -> list[Fix]:
    fixes: list[Fix] = []
    if pp.grade in ("FAIL", "WEAK"):
        fixes.append(Fix(100, "Change your Wi-Fi password to a long passphrase - four random, unrelated words."))
    elif pp.grade == "OK":
        fixes.append(Fix(30, "Consider a longer passphrase (a 4-word phrase) for extra margin."))

    by_key = {f.key: f for f in rv.findings}

    def add_from(key, bad_priority, unknown_priority, text):
        f = by_key.get(key)
        if not f:
            return
        if f.status in ("warn", "bad"):
            fixes.append(Fix(bad_priority, text))
        elif f.status == "unknown":
            fixes.append(Fix(unknown_priority, text))

    add_from("encryption", 60, 0, "Switch your router to WPA3-only if it's offered - that shuts the downgrade door.")
    add_from("wps", 90, 50, "Turn WPS off, and confirm it really turned off.")
    add_from("admin", 85, 45, "Change the router's admin password away from the sticker default.")
    add_from("firmware", 65, 42, "Update your router firmware.")
    add_from("pmf", 70, 40, "Turn on management-frame protection (802.11w / PMF) if your router offers it.")
    add_from("ssid_name", 55, 0, "Rename your network so it doesn't advertise your router's make and model.")
    add_from("guest", 58, 38, "Put smart plugs, cameras and TVs on a separate, isolated guest network.")

    if nv.twin_suspect:
        fixes.append(Fix(50, "Your network name is on several access points - confirm they're all your own (mesh), not an impostor."))

    fixes.sort(key=lambda x: x.priority, reverse=True)
    return fixes


def assemble(platform: str, pp: PassphraseVerdict, rv: RouterVerdict, nv: NearbyVerdict) -> Report:
    score = pp.points + rv.points + nv.points  # out of 100
    capped = False
    if pp.in_leaked_list:
        # A leaked passphrase is game over - cap the grade no matter what else is good.
        if score > 45:
            score = 45
            capped = True
    score = max(0, min(100, int(round(score))))
    fixes = _build_fixes(pp, rv, nv)
    return Report(platform, pp, rv, nv, score, _letter(score), capped, fixes)


def _bar(score: int, width: int = 20) -> str:
    filled = int(round(score / 100 * width))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def render(rep: Report) -> str:
    L: list[str] = []
    L.append("=" * 64)
    L.append("  Wi-Fi Security Auditor  -  report for YOUR network")
    L.append("  Signal & Byte  -  defensive, own-network only")
    L.append("=" * 64)

    # Module A
    pp = rep.pp
    L.append("")
    L.append("A. PASSWORD VERDICT  (offline - your passphrase never left this machine)")
    L.append(f"   Verdict: {pp.grade}  -  {pp.reason}")
    L.append(f"   Length {pp.length}, character pool {pp.pool}, ~{pp.bits:.0f} bits of search space.")
    if pp.in_leaked_list:
        L.append("   NOTE: it's in a public leak, so the real time is INSTANT - the")
        L.append("         brute-force figures below are academic.")
    L.append("   Estimated brute-force time:")
    for e in pp.estimates:
        tag = "measured" if e.rate.measured else "estimate"
        L.append(f"     - {e.rate.label:<40} {e.human}  ({tag})")

    # Module B
    L.append("")
    L.append(f"B. ROUTER CHECK  (platform: {rep.platform})")
    if not rep.rv.connected:
        L.append("   Not connected to Wi-Fi, or no wireless interface - connect to your own")
        L.append("   network and run again for the router checks.")
    for f in rep.rv.findings:
        src = "measured" if f.measured else "you told us"
        L.append(f"   {_STATUS_TAG[f.status]} {f.label}  ({src})")
        L.append(f"        {f.note}")

    # Module C
    L.append("")
    L.append("C. NEIGHBOURHOOD CHECK  (passive - just reading public beacons)")
    for line in rep.nv.findings:
        L.append(f"   - {line}")

    # Report card
    L.append("")
    L.append("-" * 64)
    L.append(f"  REPORT CARD:  {rep.grade}    {_bar(rep.score)}  {rep.score}/100")
    if rep.capped:
        L.append("  (Capped: a passphrase in a public leak is an instant fail, whatever else is set.)")
    L.append("-" * 64)
    if rep.fixes:
        L.append("  Fix these tonight, in order:")
        for i, fx in enumerate(rep.fixes, 1):
            L.append(f"   {i}. {fx.text}")
    else:
        L.append("  Nothing to fix - your network is in good shape. Nicely done.")
    L.append("")
    L.append("  Reminder: only ever run this on a network you own or have written")
    L.append("  permission to test. Accessing anyone else's network is a crime.")
    L.append("=" * 64)
    return "\n".join(L)
