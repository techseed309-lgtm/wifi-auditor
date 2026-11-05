# Wi-Fi Security Auditor

A small, free tool that checks **your own** home Wi-Fi the way an attacker would look at it — then tells you,
in plain language, how strong it really is and the one thing to fix first.

It runs three checks and prints a report card:

- **A · Password verdict** — is your passphrase in a public leaked-password list, and how long would it take to
  brute-force at several hardware speeds? (100% offline — your passphrase never leaves your machine.)
- **B · Router check** — what your computer already knows about the network you're on: WPA2 / WPA3, the cipher,
  and whether your network *name* leaks your router's make and model. Plus the few things only your router knows
  (WPS, management-frame protection, firmware, admin password, guest network), which it asks you to confirm.
- **C · Neighbourhood check** — a *passive* look at the networks in range for a second one using your name
  (the tell-tale of an "evil twin") and for open networks.
- **D · Report card** — a grade (A–F) and a ranked, do-it-tonight fix list.

## ⚠️ Read this first — legal and scope

This tool is a **mirror for a network you own**, not a key to anyone else's.

- Only ever run the active checks on a network you **own** or have **written permission** to test.
- Accessing or cracking a network you don't own is a **crime** (US CFAA, UK Computer Misuse Act, and equivalents
  almost everywhere).
- The password check is pure offline math. The router and neighbourhood checks only **read** your own connection
  and **passively** list networks already broadcasting in the open — they do not attack, deauth, or connect to
  anything.
- Cracking a *captured handshake* against your own router (the demo in the video) is **not** part of this tool.
  That belongs in an isolated lab on gear you own — see [`docs/LAB-DEMO.md`](docs/LAB-DEMO.md).

## Install & run

You need **Python 3.9+**. No other dependencies for the core checks.

```bash
# 1) clone
git clone https://github.com/techseed309-lgtm/wifi-auditor
cd wifi-auditor

# 2a) command line
python -m wifi_auditor

# 2b) or the double-click app (Windows): run.bat  (opens the window)
```

Optional, for a **measured** crack-rate on your exact machine: install [hashcat](https://hashcat.net/hashcat/)
and put it on your PATH. Without it, the tool uses clearly-labelled reference rates for common hardware.

For the full leaked-list check, download the public `rockyou.txt` (SecLists) and pass it with
`--wordlist path/to/rockyou.txt`. The bundled list is a small sample of the most common passwords so the tool
works out of the box.

## Three ways to use it

| Form | How | File |
|---|---|---|
| Plain script / CLI | `python -m wifi_auditor` | `wifi_auditor/` |
| Double-click Windows app | `run.bat` (or build an `.exe`, see `docs/BUILD-WINDOWS.md`) | `wifi_auditor/gui.py` |
| Claude Code / ChatGPT skill | drop `skill/` into your skills folder and ask it to audit your network | `skill/SKILL.md` |

## Platform support

- **Windows 10/11** — full (reads your connection and nearby networks via `netsh`).
- **Linux** — best-effort via `nmcli` (NetworkManager).
- **macOS** — best-effort via `system_profiler` / `wdutil`.
- The **password verdict (Module A)** is pure Python and works everywhere.

Honest note: no tool on your laptop can read your router's WPS state, firmware date or management-frame-protection
setting over the air — those live on the router. For those, the auditor asks you a few yes/no questions (or you
pass flags) and folds your answers into the grade, clearly marked as *you told us* versus *we measured*.

## Credits & licence
Built by **Signal & Byte** — "Tech news, decoded." MIT licence (see `LICENSE`). Uses only the Python standard
library. hashcat and rockyou are third-party and optional.
