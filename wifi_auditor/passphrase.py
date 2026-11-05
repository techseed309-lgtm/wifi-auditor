"""Module A - the password verdict.

Answers the scary question: would my Wi-Fi passphrase survive an offline
guessing attack? Two checks, both 100% offline - the passphrase never leaves
this machine:

  1. Is it sitting in a public leaked-password list? (instant fail if so)
  2. How long would brute force take, at several hardware speeds?

The brute-force estimate treats the passphrase as a random string drawn from the
character sets it uses. Real guessing is often *faster* than that (people aren't
random), which is exactly why the leaked-list check in step 1 matters - and why
the honest advice is length, not cleverness.
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass

from .ratecheck import Rate, get_rates

HERE = os.path.dirname(__file__)
DEFAULT_WORDLIST = os.path.join(HERE, "wordlists", "common-passwords.txt")

_YEAR_SECONDS = 365.25 * 86400
_UNIVERSE_YEARS = 1.38e10  # age of the universe, for the "longer than..." line


def _unit(value: float, unit: str) -> str:
    n = round(value)
    return f"about {n:,} {unit}{'' if n == 1 else 's'}"


def human_time(seconds: float) -> str:
    if seconds < 1:
        return "less than a second"
    if seconds < 60:
        return _unit(seconds, "second")
    if seconds < 3600:
        return _unit(seconds / 60, "minute")
    if seconds < 86400:
        return _unit(seconds / 3600, "hour")
    if seconds < _YEAR_SECONDS:
        return _unit(seconds / 86400, "day")
    years = seconds / _YEAR_SECONDS
    if years > _UNIVERSE_YEARS:
        return "longer than the universe has existed"
    if years < 1e3:
        return _unit(years, "year")
    if years < 1e6:
        return f"about {years / 1e3:,.0f} thousand years"
    if years < 1e9:
        return f"about {years / 1e6:,.0f} million years"
    return f"about {years / 1e9:,.0f} billion years"


def char_pool(pw: str) -> int:
    """Rough size of the character set the passphrase draws from."""
    pool = 0
    if any(c.islower() for c in pw):
        pool += 26
    if any(c.isupper() for c in pw):
        pool += 26
    if any(c.isdigit() for c in pw):
        pool += 10
    if any(not c.isalnum() for c in pw):
        pool += 33  # rough count of common printable symbols + space
    return pool or 1


def in_wordlist(pw: str, path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.rstrip("\r\n") == pw:
                    return True
    except OSError:
        return False
    return False


@dataclass
class TimeEstimate:
    rate: Rate
    seconds: float
    human: str


@dataclass
class PassphraseVerdict:
    length: int
    pool: int
    bits: float
    in_leaked_list: bool
    estimates: list[TimeEstimate]
    grade: str   # FAIL / WEAK / OK / STRONG
    reason: str

    @property
    def points(self) -> int:
        """0-40 contribution to the overall report-card score."""
        return {"FAIL": 0, "WEAK": 12, "OK": 28, "STRONG": 40}[self.grade]


def assess(pw: str, wordlist: str = DEFAULT_WORDLIST,
           rates: list[Rate] | None = None) -> PassphraseVerdict:
    length = len(pw)
    pool = char_pool(pw)
    leaked = in_wordlist(pw, wordlist)
    combos = pool ** length if length else 1
    bits = math.log2(combos) if combos > 1 else 0.0

    rates = rates if rates is not None else get_rates()
    estimates: list[TimeEstimate] = []
    for r in rates:
        # average brute-force work is half the keyspace
        secs = (combos / 2) / r.guesses_per_sec
        estimates.append(TimeEstimate(r, secs, human_time(secs)))

    if leaked:
        grade = "FAIL"
        reason = "This exact passphrase is in a public leaked-password list - it would fall almost instantly."
    elif length < 8:
        grade = "WEAK"
        reason = "Under 8 characters - too short; brute force gets there fast."
    elif bits < 45:
        grade = "WEAK"
        reason = "Short or simple enough to brute force on fast hardware. Make it longer."
    elif bits < 60:
        grade = "OK"
        reason = "Decent, but a determined attacker with GPUs could still get there. Longer (a 4-word phrase) is safer."
    else:
        grade = "STRONG"
        reason = "Effectively uncrackable offline with today's hardware."
    return PassphraseVerdict(length, pool, bits, leaked, estimates, grade, reason)
