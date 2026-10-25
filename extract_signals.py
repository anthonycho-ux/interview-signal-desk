#!/usr/bin/env python3
"""Extract signal evidence from Karsan transcripts (v3, distance-aware).

Themes use proximity regexes (two concepts within a short word window) so
quotes are on-topic. Wall evidence requires a numeric level near call/put/
wall/support/resistance wording.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, "transcripts.json")
OUT = os.path.join(HERE, "signals.json")

DIST = r"(?:\W+\w+){0,7}\W+"

RX = {
    # regime: gamma/hedge + signifier
    "regime": re.compile(
        r"\b(gamma|vomma|vanna|vega|hedg(?:ing|e)|optionality|dealer)\b"
        r"(?:\W+\w+){0,9}\W+"
        r"\b(short|long|negative|positive|selling|buying|pressure|amplif|fragile|vulnerable)\b", re.I),
    # walls: any numeric level with an options-ish word within ±3 words
    "wall": None,  # handled by build_wall below
    # vol posture: vol word + direction
    "vol_posture": re.compile(
        r"\b(?:vol|volatility|vix|implied)\b"
        r"(?:\W+\w+){0,9}\W+"
        r"\b(compress|expand|spike|crush|suppress|support|higher|lower|surge|balloon|blow|cheap|expensive|hot potato|long|short|buy|sell)\b", re.I),
    # opex
    "opex_stance": re.compile(
        r"\b(?:opex|expiration|expiry|third friday)\b"
        r"(?:\W+\w+){0,7}\W+"
        r"\b(?:week|big|pin|friday|flows|front|position|close|before|after)\b", re.I),
    # fed / liquidity
    "fed_liquidity": re.compile(
        r"\b(?:fed|fomc|liquidity|balance sheet|10[- ]year|yield|bond market|qe)\b"
        r"(?:\W+\w+){0,9}\W+"
        r"\b(?:meeting|pivot|involved|on board|facility|want|will|expect|cut|ease|support|suppression|control|frame)\b", re.I),
    # crash / drawdown
    "crash_call": re.compile(
        r"\b(?:crash|decline|recession|drawdown|correction|top|20%|20 %)\b", re.I),
}

THEMES = [
    ("regime", "Gamma regime", "regime"),
    ("gamma_flip", "Gamma flip / levels", None),  # corpus has no flip language; stays muted
    ("walls_skew", "Event walls & put skew", None),  # via build_wall (no numeric requirement)
    ("vol_posture", "Vol posture", "vol_posture"),
    ("opex_stance", "OpEx stance", "opex_stance"),
    ("fed_liquidity", "Fed / liquidity", "fed_liquidity"),
    ("crash_call", "Crash / drawdown view", "crash_call"),
]


LEVEL = re.compile(r"\b(?:\d{1,3}(?:,\d{3})|\d{4})\b")
WALLK = re.compile(r"\b(call|put|gamma|wall|support|resistance|strike|floor|ceiling|level|screen)\b", re.I)


def build_wall(key, label):
    # walls/skew: quotes that discuss walls or skew (no numeric requirement —
    # this window contains no explicit SPX wall levels, and inventing them
    # would be fabrication). Capture the real language instead.
    rx = re.compile(
        r"\b(?:wall|put skew|call skew|skew)\b", re.I)
    quotes = []
    for v in ok:
        for seg in v["segments"]:
            if rx.search(seg["text"]):
                quotes.append({
                    "video": v["id"], "date": v["date"],
                    "t": seg["t"], "text": seg["text"][:280],
                })
    quotes.sort(key=lambda q: (q["date"], q["t"]), reverse=True)
    seen = set()
    uniq = []
    for q in quotes:
        sig = (q["date"], q["text"][:70])
        if sig in seen:
            continue
        seen.add(sig)
        uniq.append(q)
    levels = sorted({int(n.replace(",", "")) for q in uniq
                     for n in re.findall(r"\b\d{1,3}(?:,\d{3})?\b", q["text"])
                     if len(n.replace(",", "")) == 4})
    return {"label": label, "quotes": uniq, "levels": levels,
            "latest": uniq[0] if uniq else None}


def build(key, label, pat):
    if pat is None:
        return {"label": label, "quotes": [], "latest": None}
    quotes = []
    for v in ok:
        for seg in v["segments"]:
            if pat.search(seg["text"]):
                quotes.append({
                    "video": v["id"], "date": v["date"],
                    "t": seg["t"], "text": seg["text"][:280],
                })
    quotes.sort(key=lambda q: (q["date"], q["t"]), reverse=True)
    seen = set()
    uniq = []
    for q in quotes:
        sig = (q["date"], q["text"][:70])
        if sig in seen:
            continue
        seen.add(sig)
        uniq.append(q)
    # distinct 4-digit levels mentioned inside the quotes (SPX-style)
    levels = sorted({int(n) for q in uniq
                     for n in re.findall(r"\b([0-9]{4})\b", q["text"])})
    return {"label": label, "quotes": uniq, "levels": levels,
            "latest": uniq[0] if uniq else None}


def main():
    global ok
    data = json.load(open(IN, encoding="utf-8"))
    ok = [v for v in data if v["status"] == "ok"]

    out = {}
    for key, label, rkey in THEMES:
        if key == "walls_skew":
            out[key] = build_wall(key, label)
        else:
            out[key] = build(key, label, RX[rkey] if rkey else None)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)

    for key, d in out.items():
        latest = d["latest"]
        if latest:
            print("%-14s %4d quotes  latest %s  %s" %
                  (key, len(d["quotes"]), latest["date"], latest["text"][:78]))
        else:
            print("%-14s %4d quotes  (none)" % (key, 0))


if __name__ == "__main__":
    main()
