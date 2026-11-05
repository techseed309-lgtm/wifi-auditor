"""Measure or estimate how fast a computer guesses WPA2 passphrases.

WPA2 derives its key with PBKDF2-HMAC-SHA1 over 4096 iterations - deliberately
slow. That slowness is *why* a long passphrase is so strong: even fast hardware
only makes so many guesses per second.

If hashcat is installed we measure this machine's real rate with its built-in
benchmark (mode 22000). Otherwise we fall back to clearly-labelled REFERENCE
rates for common hardware. Everything here is offline math - nothing touches a
network.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass

# Reference guess rates for WPA2 (hashcat mode 22000), guesses per second.
# LABELLED ESTIMATES - real numbers vary a lot by hardware, drivers and cooling.
# Based on public hashcat benchmark posts (2025-2026); a single RTX 4090 lands
# roughly 1.6-2.6 M H/s on WPA2, so we use ~2 M as a mid-point.
REFERENCE_RATES: dict[str, int] = {
    "A typical laptop, no GPU (CPU only)": 5_000,
    "A modern gaming GPU (RTX 4090 class)": 2_000_000,
    "A determined attacker's rig (8x GPUs)": 16_000_000,
}


@dataclass
class Rate:
    label: str
    guesses_per_sec: float
    measured: bool  # True = benchmarked on this machine; False = reference estimate


def _parse_hashcat_benchmark(text: str) -> float | None:
    """Pull the best 'Speed...: N kH/s' number out of hashcat -b output."""
    best: float | None = None
    mult = {"": 1.0, "k": 1e3, "M": 1e6, "G": 1e9, "T": 1e12}
    for m in re.finditer(r"Speed[.\#\d]*\.*:\s*([\d.]+)\s*([kMGT]?)H/s", text):
        value = float(m.group(1)) * mult[m.group(2)]
        if best is None or value > best:
            best = value
    return best


def measure_this_machine(timeout: int = 180) -> Rate | None:
    """Run hashcat's WPA2 benchmark if hashcat is on PATH; else None."""
    exe = shutil.which("hashcat")
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [exe, "-b", "-m", "22000", "--quiet"],
            capture_output=True, text=True, timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    rate = _parse_hashcat_benchmark(f"{proc.stdout}\n{proc.stderr}")
    if not rate:
        return None
    return Rate("This machine (measured with hashcat)", rate, measured=True)


def get_rates(try_measure: bool = True) -> list[Rate]:
    """This machine's measured rate first (if hashcat is present), then the
    labelled reference rates."""
    rates: list[Rate] = []
    if try_measure:
        measured = measure_this_machine()
        if measured:
            rates.append(measured)
    rates.extend(Rate(label, float(r), measured=False) for label, r in REFERENCE_RATES.items())
    return rates
