"""Command-line entry point: python -m wifi_auditor

Runs the three checks on YOUR own network and prints the report card.
"""
from __future__ import annotations

import argparse
import getpass
import sys

from . import platforms
from .passphrase import DEFAULT_WORDLIST, assess as assess_pw
from .router import RouterFacts, assess as assess_router
from .nearby import assess as assess_nearby
from .report import assemble, render


def _tri(value: str | None) -> bool | None:
    """Map a yes/no/unknown answer to True/False/None."""
    if value is None:
        return None
    v = value.strip().lower()
    if v in ("y", "yes", "on", "true", "1"):
        return True
    if v in ("n", "no", "off", "false", "0"):
        return False
    return None


def _ask(prompt: str) -> bool | None:
    try:
        return _tri(input(f"   {prompt} [y/n/?]: "))
    except (EOFError, KeyboardInterrupt):
        return None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="wifi_auditor",
        description="Audit YOUR OWN home Wi-Fi (defensive). Never run against a network you don't own.")
    p.add_argument("--passphrase", help="Your Wi-Fi passphrase (prompted securely if omitted). Never stored or sent.")
    p.add_argument("--wordlist", default=DEFAULT_WORDLIST,
                   help="Leaked-password list to check against (default: bundled sample; use rockyou.txt for the full check).")
    p.add_argument("--no-measure", action="store_true",
                   help="Skip the hashcat benchmark even if hashcat is installed.")
    p.add_argument("--non-interactive", action="store_true",
                   help="Don't prompt for router facts; use the flags below (unknown if not given).")
    p.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of the report.")
    for name, help_ in [
        ("wps", "WPS enabled on the router?"),
        ("pmf", "Management-frame protection (802.11w) on?"),
        ("admin-changed", "Router admin password changed from default?"),
        ("firmware-recent", "Firmware updated in the last few months?"),
        ("guest-isolated", "IoT devices on an isolated guest network?"),
    ]:
        p.add_argument(f"--{name}", choices=["y", "n", "?"], help=help_)
    return p


def _collect_facts(args) -> RouterFacts:
    if args.non_interactive or not sys.stdin.isatty():
        return RouterFacts(
            wps_on=_tri(args.wps),
            pmf_on=_tri(args.pmf),
            admin_changed=_tri(args.admin_changed),
            firmware_recent=_tri(args.firmware_recent),
            guest_isolated=_tri(args.guest_isolated),
        )
    print("\n A few things only your router knows (open its admin page if unsure):")
    return RouterFacts(
        wps_on=_tri(args.wps) if args.wps else _ask("Is WPS (push-button/PIN pairing) ON?"),
        pmf_on=_tri(args.pmf) if args.pmf else _ask("Is management-frame protection (802.11w/PMF) ON?"),
        admin_changed=_tri(args.admin_changed) if args.admin_changed else _ask("Did you change the admin password from the sticker default?"),
        firmware_recent=_tri(args.firmware_recent) if args.firmware_recent else _ask("Firmware updated in the last few months?"),
        guest_isolated=_tri(args.guest_isolated) if args.guest_isolated else _ask("Are IoT devices on an isolated guest network?"),
    )


def run(args) -> int:
    pw = args.passphrase
    if pw is None:
        try:
            pw = getpass.getpass("Your Wi-Fi passphrase (hidden; never stored or sent): ")
        except (EOFError, KeyboardInterrupt):
            print("\nNo passphrase entered - skipping the password verdict.")
            pw = ""

    pp = assess_pw(pw, wordlist=args.wordlist,
                   rates=None if not args.no_measure else _reference_only())
    conn = platforms.connection()
    facts = _collect_facts(args)
    rv = assess_router(conn, facts)
    nv = assess_nearby(platforms.nearby(),
                       conn.get("ssid") if conn else None,
                       conn.get("bssid") if conn else None)
    rep = assemble(platforms.platform_name(), pp, rv, nv)

    if args.json:
        print(_as_json(rep))
    else:
        print(render(rep))
    return 0


def _reference_only():
    from .ratecheck import get_rates
    return get_rates(try_measure=False)


def _as_json(rep) -> str:
    import json
    return json.dumps({
        "platform": rep.platform,
        "score": rep.score,
        "grade": rep.grade,
        "capped": rep.capped,
        "password": {
            "grade": rep.pp.grade, "length": rep.pp.length,
            "bits": round(rep.pp.bits, 1), "in_leaked_list": rep.pp.in_leaked_list,
            "estimates": [{"who": e.rate.label, "seconds": e.seconds,
                           "human": e.human, "measured": e.rate.measured}
                          for e in rep.pp.estimates],
        },
        "router": {"auth_class": rep.rv.auth_class,
                   "findings": [{"key": f.key, "status": f.status,
                                 "measured": f.measured, "note": f.note}
                                for f in rep.rv.findings]},
        "nearby": {"scanned": rep.nv.scanned, "total": rep.nv.total,
                   "twin_suspect": rep.nv.twin_suspect, "open_count": rep.nv.open_count},
        "fixes": [fx.text for fx in rep.fixes],
    }, indent=2)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
