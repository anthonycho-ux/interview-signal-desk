#!/usr/bin/env python3
"""Normalize VTT transcripts into segmented JSON.

Reads transcripts/*.en.vtt, writes transcripts.json:
  [{ id, title, date, url, status: "ok"|"missing",
     segments: [{t (sec), text}], full_text }]

Cleans VTT cue text (drops <c> markup, aligns), merges cue fragments
that are continuations of the same sentence (estimate by timing gap).
"""
import json
import os
import re
import html as htmlmod

HERE = os.path.dirname(os.path.abspath(__file__))
VTT_DIR = os.path.join(HERE, "transcripts")
INV = os.path.join(HERE, "karsan-videos.json")
OUT = os.path.join(HERE, "transcripts.json")

TAG = re.compile(r"<[^>]+>")
TIMECODE = re.compile(r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})")


def parse_ts(ts):
    m = TIMECODE.match(ts)
    if not m:
        return None
    h, mi, s, ms = map(int, m.groups())
    return h * 3600 + mi * 60 + s + ms / 1000.0


def clean(text):
    text = TAG.sub("", text)
    text = htmlmod.unescape(text)
    text = text.replace(">>", "")
    return re.sub(r"\s+", " ", text).strip()


def parse_vtt(path):
    cues = []
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    in_cue = False
    start = end = None
    buf = []
    for line in lines:
        if line.strip() == "WEBVTT" or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line:
            if in_cue and buf:
                t = clean(" ".join(buf))
                if t:
                    cues.append((start, end, t))
            m = re.match(r"(\S+) --> (\S+)", line)
            if not m:
                in_cue = False
                continue
            start = parse_ts(m.group(1))
            end = parse_ts(m.group(2))
            buf = []
            in_cue = True
        elif in_cue:
            if line.strip():
                buf.append(line)
            else:
                if buf:
                    t = clean(" ".join(buf))
                    if t:
                        cues.append((start, end, t))
                    buf = []
                    in_cue = False
    if in_cue and buf:
        t = clean(" ".join(buf))
        if t:
            cues.append((start, end, t))

    # de-duplicate: auto-caption VTT repeats each phrase twice, once with
    # per-word <c> markup and once clean; keep only the first occurrence
    # (same text, overlapping time) and skip the duplicate line.
    dedup = []
    for start, end, text in cues:
        if dedup:
            p_start, p_end, p_text = dedup[-1]
            same = text == p_text or (p_text and text and text in p_text)
            overlapping = (start is not None and p_end is not None and start < p_end + 0.3)
            if same and overlapping:
                continue
        dedup.append((start, end, text))
    cues = dedup

    # merge continuation cues: same sentence continues when the gap from
    # previous end to next start is tiny (< 0.5s) and no terminal punctuation
    #
    # YouTube auto-captions repeat the previous cue's tail at the head of the
    # next cue (rolling captions). Strip that repeated prefix before merging
    # so sentences read once.
    def strip_rolling_prefix(prev, nxt):
        pw = prev.split()
        nw = nxt.split()
        best = 0
        for k in range(min(len(pw), len(nw)), 0, -1):
            if pw[-k:] == nw[:k]:
                best = k
                break
        if best >= 3:
            rest = " ".join(nw[best:])
            return re.sub(r"^[\s,;:]+", "", rest)
        return nxt

    merged = []
    for start, end, text in cues:
        if merged:
            p_start, p_end, p_text = merged[-1]
            gap = start - p_end if (start is not None and p_end is not None) else 0
            if gap < 0.5 and not p_text.endswith((".", "!", "?", "…")):
                text = strip_rolling_prefix(p_text, text)
                if not text:
                    continue
                merged[-1] = (p_start, end, p_text + " " + text)
                continue
        merged.append((start, end, text))

    return [{"t": round(s, 2) if s is not None else None, "text": t} for s, _, t in merged]


def main():
    inv = json.load(open(INV, encoding="utf-8"))
    out = []
    for v in inv:
        vid = v["id"]
        path = os.path.join(VTT_DIR, vid + ".en.vtt")
        if os.path.exists(path) and os.path.getsize(path) > 0:
            segs = parse_vtt(path)
            full = " ".join(s["text"] for s in segs)
            out.append({
                "id": vid, "title": v["title"], "date": v.get("date", ""),
                "url": v.get("url", ""), "status": "ok",
                "segments": segs, "full_text": full,
            })
        else:
            out.append({
                "id": vid, "title": v["title"], "date": v.get("date", ""),
                "url": v.get("url", ""), "status": "missing",
                "segments": [], "full_text": "",
            })

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))

    ok = sum(1 for x in out if x["status"] == "ok")
    words = sum(len(x["full_text"].split()) for x in out)
    print("transcripts: %d ok / %d total, %d words" % (ok, len(out), words))


if __name__ == "__main__":
    main()
