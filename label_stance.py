#!/usr/bin/env python3
"""Provisional per-quote stance labels for the Karsan signal desk.

Sign convention (uniform across every theme): dir > 0 means the quote presses
the theme harder than neutral (urgency, extremity, imminence); dir < 0 means it
deflates it (contained, gradual, mild, later). This is claim intensity, NOT
bullish/bearish. It is a keyword prior, marked src=auto, and is meant to be
corrected by hand in the desk.

Writes stance.json keyed by "video:rounded_t" so it survives regeneration of
signals.json by extract_signals.py (which rewrites that file wholesale).
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SIG = os.path.join(HERE, "signals.json")
OUT = os.path.join(HERE, "stance.json")

# words that read directional but are not (risk, now, support, bid, hit, down,
# ok, fine, hold) are deliberately excluded: a false label is worse than a
# missing one on a first pass.
STEMS = {"deleverag", "stabiliz", "accelerat", "capitulat", "escalat"}

# weight 2 = unambiguous extremity, 1 = directional pressure
ESC = {
    2: ["crash", "collapse", "selloff", "sell-off", "plunge", "capitulat",
        "panic", "blow up", "blowup", "meltdown", "catastroph",
        "unprecedented", "extreme", "violent", "brutal", "severe", "forced",
        "unwind", "deleverag", "no bid", "free fall", "freefall",
        "unsustainable", "dangerous", "fragile", "broken", "whacked", "trap"],
    1: ["decline", "drawdown", "correction", "recession", "tail risk",
        "downside", "worse", "worst", "massive", "huge", "spike", "elevated",
        "accelerat", "imminent", "squeeze", "pain", "tightening", "escalat",
        "already"],
}

SOFT = {
    2: ["soft landing", "no recession", "not worried", "no crash",
        "buy the dip", "contained", "benign"],
    1: ["resilient", "stable", "stabiliz", "calm", "gradual", "mild",
        "modest", "limited", "later", "recovery", "recover", "rally",
        "relief", "easing", "pause", "muted", "healthy", "constructive",
        "compressed", "suppressed", "cheap"],
}

NEG = re.compile(r"\b(no|not|never|isn'?t|aren'?t|won'?t|don'?t|doesn'?t)\b"
                 r"(?:\W+\w+){0,3}\W+$", re.I)


def pattern(term):
    body = re.escape(term)
    return r"\b" + body + (r"\w*" if term in STEMS else r"\b")


def score(text):
    low = " " + text.lower() + " "
    hits = []
    val = 0
    for w, words in ESC.items():
        for term in words:
            for m in re.finditer(pattern(term), low):
                neg = bool(NEG.search(low[max(0, m.start() - 24):m.start()]))
                val += (-w if neg else w)
                hits.append(("-" if neg else "+") + term)
    for w, words in SOFT.items():
        for term in words:
            for m in re.finditer(pattern(term), low):
                neg = bool(NEG.search(low[max(0, m.start() - 24):m.start()]))
                val += (w if neg else -w)
                hits.append(("+" if neg else "-") + term)
    return max(-2, min(2, val)), hits[:4]


def main():
    data = json.load(open(SIG, encoding="utf-8"))
    out = {"_note": "provisional keyword-prior stance; dir>0 presses the theme "
                    "harder, dir<0 deflates it. claim intensity, not bullish/bearish. "
                    "src=auto means unconfirmed.",
           "_schema": "video:rounded_seconds -> {dir, hits, src}",
           "themes": {}}
    n = 0
    nonzero = 0
    for theme, blob in data.items():
        out["themes"][theme] = {"label": blob.get("label"), "quotes": {}}
        for q in blob.get("quotes", []):
            key = "%s:%d" % (q["video"], round(float(q["t"])))
            d, hits = score(q.get("text", ""))
            out["themes"][theme]["quotes"][key] = {
                "dir": d, "hits": hits, "src": "auto",
                "date": q.get("date"), "text": q.get("text", "")[:160],
            }
            n += 1
            if d:
                nonzero += 1
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("quotes labelled: %d  non-zero: %d (%.0f%%)  -> %s"
          % (n, nonzero, 100.0 * nonzero / max(1, n), OUT))


if __name__ == "__main__":
    main()
