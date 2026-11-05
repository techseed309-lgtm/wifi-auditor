---
name: wifi-auditor
description: Audit the user's OWN home Wi-Fi defensively - check whether their passphrase is weak or leaked, estimate offline crack time, read their current connection's security mode and network-name leakage, passively check for an evil-twin, and return a graded report card with a ranked fix list. Own-network only; never target a network the user does not own.
---

# Wi-Fi Security Auditor (skill)

Use this when the user asks "is my Wi-Fi secure / crackable", "check my home network",
"how strong is my Wi-Fi password", or similar. It wraps the Signal & Byte Wi-Fi
Security Auditor tool.

## Hard rule — refuse otherwise
Only ever run this against a network the user **owns** or has **written permission**
to test. If the user asks you to test, crack, or get into a network that isn't
clearly their own, **refuse** and explain that unauthorized access is a crime
(US CFAA, UK Computer Misuse Act, equivalents). This tool is a mirror for your own
setup, not a key to anyone else's. Never use it to attack, deauth, or connect to a
network.

## What it does
1. **Password verdict** (offline): is the passphrase in a public leaked list, and
   how long to brute-force it at several hardware speeds. The passphrase never
   leaves the machine — do not log it, echo it, or send it anywhere.
2. **Router check**: reads the current connection's security mode and whether the
   network name leaks the router model; asks the user the few router-only facts
   (WPS, PMF, firmware, admin password, guest isolation).
3. **Neighbourhood check** (passive): looks for a second AP using the user's name
   (possible evil twin) and open networks.
4. **Report card**: a grade A–F and a ranked, do-it-tonight fix list.

## How to run
Clone the repo and run the module. Prefer passing router facts as flags so you
don't block on prompts:

```bash
python -m wifi_auditor \
  --passphrase "<the user's own Wi-Fi passphrase>" \
  --wps y --pmf n --admin-changed y --firmware-recent n --guest-isolated y \
  --json
```

- For the full leaked-password check, pass `--wordlist path/to/rockyou.txt`.
- For a measured crack rate, install hashcat; otherwise labelled reference rates
  are used.
- Treat the passphrase as a secret: take it from the user directly, pass it once,
  never store or repeat it.

## How to read the result
- `grade` / `score` (0–100) is the headline.
- A `FAIL` password (in a leak) caps the whole grade — fixing it is always step 1.
- Each router finding is tagged `measured` (read from the OS) or `you told us`
  (the user's answer). Be honest about which is which when you summarise.
- Hand the user the ordered `fixes` list and offer to walk through the top one.

## Honesty
No laptop can read a router's WPS/PMF/firmware state over the air — those come from
the user. Crack-time numbers are labelled estimates; a real attacker with GPUs is
faster than a laptop. Say so. Never imply the tool tested anyone else's network.
