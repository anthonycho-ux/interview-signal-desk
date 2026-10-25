#!/usr/bin/env python3
"""Build the bilingual one-page briefing for retail ('pajama') traders.

Consumes the Gemini draft (pajama-draft.txt) plus the desk evidence
(signals.json), and emits pajama/index.html with:
  - the generated bilingual sections (English + Korean),
  - an evidence rail with the verbatim Karsan quotes behind the claims,
  - a source note and a not-advice line.
"""
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFT = os.path.join(HERE, "pajama-draft.txt")
SIG = os.path.join(HERE, "signals.json")
OUT = os.path.join(HERE, "pajama", "index.html")

HANGUL = re.compile(r"[가-힣]")


def lang_of(line):
    return "kr" if HANGUL.search(line) else "en"

LABEL = {
    "regime": "regime",
    "gamma_flip": "gamma flip",
    "walls_skew": "walls & skew",
    "vol_posture": "vol posture",
    "opex_stance": "opex stance",
    "fed_liquidity": "fed & liquidity",
    "crash_call": "base case",
}

HEAD = re.compile(r"^\s*(\d+)\.\s+(.+)$")


def is_heading(line):
    # heading lines carry a bilingual title (EN / KR) and no terminal period,
    # or are explicitly numbered.
    if HEAD.match(line):
        return True
    return "/" in line and len(line) < 90 and not line.rstrip().endswith(".")


def esc(s):
    return html.escape(s, quote=False)


def parse_draft():
    lines = open(DRAFT, encoding="utf-8").read().splitlines()
    blocks = []
    cur = None  # [heading, paragraphs[]]
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if is_heading(line):
            if cur:
                blocks.append(cur)
            m = HEAD.match(line)
            cur = [m.group(2).strip() if m else line, []]
            continue
        if not cur:
            continue
        cur[1].append(line)
    if cur:
        blocks.append(cur)
    return blocks


def evidence_rail():
    sig = json.load(open(SIG, encoding="utf-8"))
    items = []
    for k, label in LABEL.items():
        t = sig.get(k) or {}
        q = t.get("latest")
        if not q:
            continue
        items.append((label, q["date"], q["text"][:200]))
    return items


def render():
    blocks = parse_draft()
    rail = evidence_rail()

    sections = []
    for heading, paras in blocks:
        body = "".join('<p class="%s">%s</p>' % (lang_of(p), esc(p)) for p in paras)
        sections.append(
            '<section class="sec"><h3>%s</h3>%s</section>' % (esc(heading), body))

    rail_html = "".join(
        '<div class="ev"><span class="d">%s</span><span class="lbl">%s</span>'
        '<span class="qt">“%s…”</span></div>' % (esc(d), esc(l), esc(t))
        for l, d, t in rail)

    page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pajama trader briefing</title>
<style>
  :root {
    color-scheme: light;
    --surface-1: #fcfcfb; --surface-2: #f4f4f1; --page: #f9f9f7;
    --ink-1: #0b0b0b; --ink-2: #52514e; --ink-3: #898781;
    --hair: #e1e0d9; --axis: #c3c2b7; --accent: #2a78d6;
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) {
      --surface-1: #1a1a19; --surface-2: #262625; --page: #0d0d0d;
      --ink-1: #f0efec; --ink-2: #c3c2b7; --ink-3: #898781;
      --hair: #2c2c2a; --axis: #383835; --accent: #3987e5;
    }
  }
  :root[data-theme="dark"] {
    --surface-1: #1a1a19; --surface-2: #262625; --page: #0d0d0d;
    --ink-1: #f0efec; --ink-2: #c3c2b7; --ink-3: #898781;
    --hair: #2c2c2a; --axis: #383835; --accent: #3987e5;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--page); color: var(--ink-1);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    font-size: 15px; line-height: 1.6; }
  .wrap { max-width: 1080px; margin: 0 auto; padding: 36px 20px 90px;
    display: grid; grid-template-columns: minmax(0,1fr) 340px; gap: 26px; }
  .top { grid-column: 1 / -1; display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
  h1 { font-size: 24px; margin: 0 0 4px; letter-spacing: -0.015em; }
  .sub { color: var(--ink-2); font-size: 13.5px; margin: 0; }
  .langsw { margin-left: auto; display: inline-flex; border: 1px solid var(--hair);
    border-radius: 8px; overflow: hidden; font-size: 13px; }
  .langsw button { font: inherit; border: 0; background: var(--surface-1);
    color: var(--ink-2); padding: 6px 14px; cursor: pointer; }
  .langsw button.on { background: var(--accent); color: #fff; }
  .sec { margin-bottom: 26px; }
  .sec h3 { font-size: 13px; letter-spacing: 0.03em; text-transform: uppercase;
    color: var(--accent); margin: 0 0 8px; }
  .sec p { margin: 0 0 14px; }
  .rail { background: var(--surface-1); border: 1px solid var(--hair);
    border-radius: 10px; padding: 16px; align-self: start; }
  .rail h2 { font-size: 12px; letter-spacing: 0.04em; text-transform: uppercase;
    color: var(--ink-3); font-weight: 600; margin: 0 0 10px; }
  .ev { padding: 9px 0; border-top: 1px solid var(--hair); font-size: 13px; }
  .ev .lbl { display: block; color: var(--ink-3); font-size: 11px;
    text-transform: uppercase; letter-spacing: 0.04em; margin: 2px 0; }
  .ev .d { color: var(--accent); font-size: 11.5px; font-variant-numeric: tabular-nums; }
  .ev .qt { display: block; color: var(--ink-2); margin-top: 2px; }
  .note { margin-top: 18px; font-size: 12px; color: var(--ink-3); }
  body[data-lang="en"] .kr, body[data-lang="kr"] .en { display: none; }
  @media (max-width: 860px) {
    .wrap { grid-template-columns: 1fr; }
    .langsw { margin-left: 0; }
  }
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div>
      <h1>Pajama trader briefing</h1>
      <p class="sub">Plain-language read of the Karsan signal · for the evening trader</p>
    </div>
    <div class="langsw" id="langsw">
      <button data-l="both" class="on">EN+KR</button>
      <button data-l="en">EN</button>
      <button data-l="kr">KR</button>
    </div>
  </div>
  <div>
    %s
    <p class="note">Generated with Gemini from the desk's evidence box. Quotes are verbatim from Cem Karsan interviews (last 30 days). Not investment advice; information only.</p>
  </div>
  <aside class="rail">
    <h2>The evidence behind this</h2>
    %s
  </aside>
</div>
<script>
(() => {
  const sw = document.getElementById("langsw");
  const set = l => {
    document.body.dataset.lang = l;
    [...sw.children].forEach(b => b.classList.toggle("on", b.dataset.l === l));
    try { localStorage.setItem("pajama-lang", l); } catch (e) {}
  };
  sw.addEventListener("click", e => {
    const b = e.target.closest("button");
    if (b) set(b.dataset.l);
  });
  let saved = null;
  try { saved = localStorage.getItem("pajama-lang"); } catch (e) {}
  const q = new URLSearchParams(location.search).get("lang");
  if (q && ["en", "kr", "both"].includes(q)) saved = q;
  if (saved && ["en", "kr", "both"].includes(saved)) set(saved);
})();
</script>
</body>
</html>
""" % ("".join(sections), rail_html)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("wrote", OUT, len(page), "bytes")


if __name__ == "__main__":
    render()
