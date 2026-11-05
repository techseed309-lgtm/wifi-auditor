# Lab demo: cracking a handshake on YOUR OWN router (weak vs strong)

This is the "proof" demo from the video (beat B9). It is **not** part of the
auditor tool and it is **not** for anyone else's network. It shows, on gear you
own, that the only thing standing between a recorded handshake and your password
is the password's length.

## ⚠️ Rules — read before you touch anything
- Use a router **you own**, set up as an **isolated test lab**, with nothing else
  connected and no internet uplink. Capture only **your own** device's handshake.
- Doing any of this to a network or device you don't own, or without written
  permission, is a **crime** (US CFAA, UK Computer Misuse Act, equivalents).
- This exists to teach defence. Keep the captures and cracked passwords to the lab
  and delete them after.

## What you need
- A spare router (or a guest SSID on your own router) to use as the target.
- A second phone/laptop that is yours, to act as the "client" that connects.
- A Linux machine (or a bootable USB) with a Wi-Fi adapter that supports monitor
  mode, and `hcxdumptool` + `hcxpcapngtool` (from the hcxtools project) and
  `hashcat`. On Windows you can do the cracking step with hashcat once you have a
  capture file.

## Steps (own lab only)
1. **Set a deliberately weak password** on your test router, e.g. a single
   dictionary word, and connect your own phone to it.
2. **Capture your own handshake.** On your Linux box, put the adapter in monitor
   mode and record the handshake for *your* test SSID/BSSID while your own phone
   reconnects. Convert the capture to hashcat's `.hc22000` format with
   `hcxpcapngtool`.
   - You are only ever capturing the handshake of **your** device on **your** AP.
3. **Crack it with the tool's math made real:**
   ```bash
   hashcat -m 22000 capture.hc22000 /path/to/rockyou.txt
   ```
   The weak password falls — seconds to minutes on a normal machine, because it's
   in the wordlist. Film the clock. This is the ~4-minute result in the cold open.
4. **Now change the router to a long passphrase** — four random, unrelated words.
   Re-capture your own handshake and run the **exact same command** again:
   ```bash
   hashcat -m 22000 capture-strong.hc22000 /path/to/rockyou.txt
   # then a brute-force attempt:
   hashcat -m 22000 -a 3 capture-strong.hc22000 ?a?a?a?a?a?a?a?a?a?a?a?a
   ```
   It exhausts the wordlist with no hit, and the brute-force estimate climbs past
   any realistic time. Same attacker, same tool, same router — only the password
   changed.

## Capture for the edit
- Keep the two hashcat runs (weak hit / strong no-hit) as screen recordings and
  keep the raw logs in `files/episodes/2026-11-09-wifi-audit/prod/tool-runs/` as
  the honesty evidence (weekly-formats §5: real runs only).
- On screen, show only the **lab** SSID (something like `SB-LAB-TEST`), never your
  real home network name.

## If you can't run the full capture
The video still stands on the auditor's own output and the offline math. A fallback
is to crack a handshake capture **you generated yourself** in the lab and that you
are free to share; do not use any third-party capture file.

## Every method, on our own lab only (owner 2026-11-03: "try every method possible")
Same hard rule, no exceptions: a router **we own**, isolated, our own devices, nothing else connected. These exist to
show viewers what each door looks like *when it's open* and how to shut it — a defensive tour, not an attack guide. The
shipped auditor stays a **passive checker** (it flags each door); it is **not** a point-and-shoot attacker (D-126). Each
demo has the same shape: open the door on our own gear → show the fix → re-test, now closed. On screen, only our lab
SSID (e.g. `SB-LAB-TEST`), never a real home network; tick "altered/synthetic content" for any AI clip; credit tools.

1. **Offline guessing** (the steps above): our own handshake → `hashcat -m 22000` with rockyou. Weak falls, strong
   holds. **Fix:** long passphrase / WPA3-only.
2. **WPS PIN + Pixie Dust** — the headline "it's not just the password": with **WPS on and a strong password**, the WPS
   PIN path (Reaver) / Pixie-Dust (weak RNG) recovers the key *despite* the strong password. Turn WPS off, re-test → it
   fails. The vivid proof that length alone isn't enough.
3. **Default / ISP-derived key**: set our router to a default-pattern SSID; show how a default-key generator or public
   default-credential list derives/looks up the key. **Fix:** change the key, rename the SSID.
4. **Evil twin + captive portal**: a second AP with our own network's name + a fake "re-enter your Wi-Fi password" page,
   on our lab; our own test phone connects and we watch the typed password captured. **Fix:** WPA3-only + PMF; never
   type the Wi-Fi password into a web page.
5. **Router admin with default creds**: log into our test router's admin page with the sticker default and read the
   Wi-Fi password straight off. **Fix:** change the admin password.
6. **WPA2/WPA3 transition downgrade**: on our mixed-mode test AP, force the WPA2 path, then the offline guess from #1
   applies. **Fix:** WPA3-only.

**KRACK:** mention only — it decrypts/injects traffic, does **not** recover the key, and is patched on current gear. No demo.

Capture each as short lab footage; keep every log in the episode `prod/` as honesty evidence (weekly-formats §5). The
auditor's report card already flags all six doors — the demos just prove what an open one costs.
