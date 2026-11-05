# Build the double-click Windows app (.exe)

Ship the auditor as a single `WiFiAuditor.exe` so viewers who don't have Python can
just double-click it.

## One-time setup
```bash
python -m pip install --upgrade pyinstaller
```

## Build (run from the repo root)
```bash
pyinstaller --noconfirm --onefile --windowed ^
  --name WiFiAuditor ^
  --add-data "wifi_auditor/wordlists/common-passwords.txt;wifi_auditor/wordlists" ^
  --collect-submodules wifi_auditor ^
  -p . ^
  launch_gui.py
```

Where `launch_gui.py` is a tiny entry script in the repo root:
```python
from wifi_auditor.gui import main
main()
```

Notes:
- `--windowed` hides the console (it's a GUI). Drop it if you want to see tracebacks.
- The `--add-data` line bundles the sample wordlist. On macOS/Linux use `:` instead
  of `;` as the separator.
- The `.exe` lands in `dist/WiFiAuditor.exe`. That's the file viewers double-click.
- hashcat is **not** bundled (it's a separate, large download). Without it the app
  uses labelled reference rates, which is fine for the password verdict.

## Smoke test the build
```bash
dist\WiFiAuditor.exe
```
The window should open, accept a passphrase, and print a report card.

## Signing (optional)
Unsigned exes trigger SmartScreen. For a public release, sign with an Authenticode
certificate, or tell viewers to prefer the `python -m wifi_auditor` route if they're
wary of an unsigned binary. Never ask viewers to disable security software.
