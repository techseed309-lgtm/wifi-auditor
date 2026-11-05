"""The double-click app (Tkinter). Launch with run.bat or:  python -m wifi_auditor.gui

A small window: type your passphrase, answer the five router questions, hit
Run audit, read the report card. Nothing leaves your machine.
"""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

from . import platforms
from .passphrase import assess as assess_pw
from .ratecheck import get_rates
from .router import RouterFacts, assess as assess_router
from .nearby import assess as assess_nearby
from .report import assemble, render

_TRI = {"unknown": None, "yes": True, "no": False}

_FACTS = [
    ("wps", "WPS (push-button/PIN pairing) is ON?"),
    ("pmf", "Management-frame protection (802.11w) is ON?"),
    ("admin", "Admin password changed from the sticker default?"),
    ("firmware", "Firmware updated in the last few months?"),
    ("guest", "IoT devices on an isolated guest network?"),
]


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Wi-Fi Security Auditor - Signal & Byte")
        self.geometry("860x660")
        self.minsize(720, 560)
        self._build()

    def _build(self) -> None:
        pad = {"padx": 10, "pady": 4}
        head = ttk.Frame(self)
        head.pack(fill="x", **pad)
        ttk.Label(head, text="Audit YOUR OWN Wi-Fi only. Testing a network you don't own is a crime.",
                  foreground="#b00000").pack(anchor="w")

        row = ttk.Frame(self)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="Your Wi-Fi passphrase:").pack(side="left")
        self.pw = tk.StringVar()
        self.pw_entry = ttk.Entry(row, textvariable=self.pw, show="*", width=30)
        self.pw_entry.pack(side="left", padx=6)
        self.show = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="show", variable=self.show, command=self._toggle).pack(side="left")
        self.measure = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="measure speed with hashcat (if installed; slower)",
                        variable=self.measure).pack(side="left", padx=10)

        facts = ttk.LabelFrame(self, text="A few things only your router knows (open its admin page if unsure)")
        facts.pack(fill="x", **pad)
        self.fact_vars: dict[str, tk.StringVar] = {}
        for key, label in _FACTS:
            fr = ttk.Frame(facts)
            fr.pack(fill="x", padx=8, pady=2)
            ttk.Label(fr, text=label, width=52).pack(side="left")
            v = tk.StringVar(value="unknown")
            self.fact_vars[key] = v
            ttk.Combobox(fr, textvariable=v, values=["unknown", "yes", "no"],
                         width=10, state="readonly").pack(side="left")

        btns = ttk.Frame(self)
        btns.pack(fill="x", **pad)
        self.run_btn = ttk.Button(btns, text="Run audit", command=self._run)
        self.run_btn.pack(side="left")
        self.status = ttk.Label(btns, text="")
        self.status.pack(side="left", padx=10)

        self.out = scrolledtext.ScrolledText(self, wrap="word", font=("Consolas", 10))
        self.out.pack(fill="both", expand=True, **pad)

    def _toggle(self) -> None:
        self.pw_entry.config(show="" if self.show.get() else "*")

    def _run(self) -> None:
        self.run_btn.config(state="disabled")
        self.status.config(text="Auditing...")
        self.out.delete("1.0", "end")
        threading.Thread(target=self._work, daemon=True).start()

    def _work(self) -> None:
        try:
            pw = self.pw.get()
            rates = get_rates(try_measure=self.measure.get())
            pp = assess_pw(pw, rates=rates)
            conn = platforms.connection()
            facts = RouterFacts(
                wps_on=_TRI[self.fact_vars["wps"].get()],
                pmf_on=_TRI[self.fact_vars["pmf"].get()],
                admin_changed=_TRI[self.fact_vars["admin"].get()],
                firmware_recent=_TRI[self.fact_vars["firmware"].get()],
                guest_isolated=_TRI[self.fact_vars["guest"].get()],
            )
            rv = assess_router(conn, facts)
            nv = assess_nearby(platforms.nearby(),
                               conn.get("ssid") if conn else None,
                               conn.get("bssid") if conn else None)
            text = render(assemble(platforms.platform_name(), pp, rv, nv))
        except Exception as e:  # keep the window alive, show the error
            text = f"Something went wrong: {type(e).__name__}: {e}"
        self.after(0, lambda: self._done(text))

    def _done(self, text: str) -> None:
        self.out.insert("1.0", text)
        self.status.config(text="Done.")
        self.run_btn.config(state="normal")


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
