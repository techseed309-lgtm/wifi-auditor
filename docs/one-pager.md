# Lock your home Wi-Fi tonight — the 7-step checklist

The whole video on one page. Do #1 and most of the risk is gone; do all seven and
nothing shown in the video gets through. (For your own network only.)

1. **Long passphrase.** Change your Wi-Fi password to **four random, unrelated
   words** (e.g. `violin-cactus-harbor-ellipse`). Length beats symbols, and you'll
   actually remember it.
2. **WPA3-only** if your router offers it. That shuts the "downgrade to WPA2" door
   and stops the offline-guessing game entirely.
3. **Turn WPS off** — and confirm it really turned off. Its PIN has been crackable
   for over a decade.
4. **Management-frame protection on** (802.11w / "PMF"). It blunts the deauth and
   knock-off attacks a fake router uses.
5. **Change the admin password** away from the sticker default, and **rename your
   network** so it doesn't advertise your router's make and model.
6. **Guest network for gadgets.** Put smart plugs, cameras and TVs on a separate,
   isolated guest network so one cheap device can't reach your main one.
7. **Update the firmware.** Old firmware ships known holes; most routers can
   auto-update — switch it on.

Check yourself any time with the free tool: `python -m wifi_auditor`
(repo: github.com/techseed309-lgtm/wifi-auditor)

---
Signal & Byte — "Tech news, decoded." Audit your own network only; testing one you
don't own is a crime.
