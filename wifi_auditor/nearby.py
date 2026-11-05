"""Module C - the neighbourhood check (passive).

Lists the networks already broadcasting in range and looks for two things:
  * a second access point using YOUR network name - the tell-tale of an "evil
    twin" (though it's often just your own mesh node or range extender);
  * open networks nearby (context only).

This only reads beacons that are public by design. It does not connect to,
probe, or deauthenticate anything.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NearbyVerdict:
    scanned: bool
    total: int
    twin_suspect: bool
    twin_note: str
    open_count: int
    points: int
    max_points: int = 20
    findings: list[str] = field(default_factory=list)


def assess(nets: list[dict], my_ssid: str | None, my_bssid: str | None) -> NearbyVerdict:
    if not nets:
        return NearbyVerdict(
            scanned=False, total=0, twin_suspect=False,
            twin_note="Couldn't scan nearby networks on this OS - skip or run the Windows version.",
            open_count=0, points=12,  # neutral/unknown
            findings=["Nearby scan unavailable on this platform."])

    total = len(nets)
    open_count = 0
    my_ap_count = 0  # how many access points broadcast OUR network name

    for n in nets:
        auth = (n.get("auth") or "").lower()
        if not auth or "open" in auth or auth in ("none", "80211open"):
            open_count += 1
        if my_ssid and n.get("ssid") == my_ssid:
            my_ap_count = max(my_ap_count, len(n.get("bssids", [])) or 1)

    findings = [f"{total} network{'' if total == 1 else 's'} visible in range."]
    if open_count:
        findings.append(f"{open_count} open (no-password) network{'' if open_count == 1 else 's'} "
                        "nearby - avoid joining those.")

    # A duplicate network name is only suspicious in unusual numbers: one router
    # commonly shows two BSSIDs (2.4 + 5 GHz), and a mesh shows several. We report
    # honestly and only raise a flag when there are clearly more than a normal
    # dual-band setup would explain.
    twin_suspect = False
    if not my_ssid:
        points = 16
        twin_note = "Not connected (or couldn't read your network) - skipped the duplicate-name check."
    elif my_ap_count == 0:
        points = 20
        twin_note = "Didn't see your own network name in the scan (it may be hidden) - nothing to flag."
    elif my_ap_count == 1:
        points = 20
        twin_note = "No stray access point is using your network name. Good."
    elif my_ap_count == 2:
        points = 18
        twin_note = ("Your network name appears on 2 access points - normal for a dual-band router or a "
                     "mesh. Only a worry if you don't run that.")
    else:
        points = 15
        twin_suspect = True
        twin_note = (f"Your network name is on {my_ap_count} access points. Fine if that's your mesh - but "
                     "if you don't run that many, treat the extras as a possible evil twin and investigate.")
    findings.append(twin_note)

    return NearbyVerdict(True, total, twin_suspect, twin_note, open_count, points,
                         findings=findings)
