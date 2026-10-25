#!/usr/bin/env python3
"""Build the Karsan radio bulletin script from the compressed signal.

Reads signals.json (theme evidence) and gamma-terrain.json (market state:
spot / flip / walls / regime). Produces radio-script.json as a list of
segments {kind, text} where text is either a grounded host line (numbers
only, trader lingo) or a verbatim Karsan quote. The segment list drives
both the TTS render and the radio page's "what you're hearing" panel.

Usage: python3 radio_script.py
"""
import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)          # karsan-inventory/
GAMMA_JSON = os.path.expanduser("~/web/gamma/gamma-terrain.json")
SIG_JSON = os.path.join(PROJ, "signals.json")
OUT = os.path.join(HERE, "radio-script.json")

THEME_LABEL = {
    "regime": "regime",
    "gamma_flip": "gamma flip",
    "walls_skew": "walls and skew",
    "vol_posture": "vol posture",
    "opex_stance": "opex stance",
    "fed_liquidity": "fed and liquidity",
    "crash_call": "base case",
}

# Host lines must only assert numbers/levels from the data, not invented
# interpretations. Longer editorial lines are left to the quotes.


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def fmt_num(v, nd=0):
    if v is None:
        return "unknown"
    return f"{v:,.{nd}f}"


def build():
    sig = load_json(SIG_JSON) or {}
    gamma = load_json(GAMMA_JSON) or {}

    now = datetime.now()  # local (MDT) — the bulletin's date should read local
    date_str = now.strftime("%A, %B %-d")  # e.g. Saturday, October 24
    segs = []

    # intro: grounded market state
    intro = [f"It's {date_str}. Karsan's options desk, on the air."]
    if gamma:
        spot = gamma.get("spot")
        flip = gamma.get("gammaFlip")
        regime = gamma.get("regime", "")
        state = []
        if spot:
            state.append(f"SPX trading near {fmt_num(spot, 2)}")
        if flip is not None:
            pct = gamma.get("flipDistancePct")
            pct_s = f", {fmt_num(pct, 2)} percent above spot" if pct is not None else ""
            state.append(f"gamma flip at {fmt_num(flip)}{pct_s}")
        if regime:
            state.append(regime.rstrip("."))
        if state:
            intro.append(" ".join(state).capitalize() + ".")
    segs.append({"kind": "intro", "text": " ".join(intro)})

    # theme blocks: host line (only when numbers exist) + latest verbatim quote
    for key, label in THEME_LABEL.items():
        theme = sig.get(key) or {}
        latest = theme.get("latest")
        quotes = theme.get("quotes") or []
        if not latest:
            continue
        block = []
        # grounded host line per theme, numbers only
        if key == "gamma_flip" and gamma and gamma.get("gammaFlip") is not None:
            flip = gamma["gammaFlip"]
            block.append(f"On the flip: {fmt_num(flip)}.")
        elif key == "regime" and gamma:
            r = gamma.get("regime")
            if r:
                block.append(r.rstrip(".") + ".")
        if block or (key == "crash_call" and latest):
            pass
        # the quote is the heart — verbatim
        block.append(f'On {label}, Karsan: "{latest["text"].strip()}"')
        segs.append({"kind": "theme", "theme": key, "text": " ".join(block)})

    # shift note: factual, no synthesis
    dated = []
    for key, label in THEME_LABEL.items():
        theme = sig.get(key) or {}
        qs = theme.get("quotes") or []
        if qs:
            dates = [q["date"] for q in qs]
            dated.append(f"{label} spoken across {len(qs)} clips, oldest {dates[-1]}, latest {dates[0]}")
    if dated:
        segs.append({"kind": "shift",
                     "text": "Across the month: " + "; ".join(dated) + "."})

    segs.append({"kind": "outro",
                 "text": "That's this week's compressed signal. The full transcript desk is open at the Karsan signal desk."})

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"renderedAt": now.isoformat(), "segments": segs},
                  fh, ensure_ascii=False, indent=1)

    words = sum(len(s["text"].split()) for s in segs)
    print("segments:", len(segs), "| words:", words, "| ~%ds at ~150wpm" % (words * 60 // 150))
    return segs


if __name__ == "__main__":
    build()
