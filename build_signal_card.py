#!/usr/bin/env python3
"""Build the Karsan signal card — a camera-ready trader's visual.

Grounds every number in gamma-terrain.json; the evidence strip quotes
verbatim from signals.json. Dark terminal paper, diverging red/blue,
one orchestrated reveal, no card-kit chrome.
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GAMMA = os.path.join(HERE, "gamma-terrain.json")
SIG = os.path.join(HERE, "signals.json")
OUT = os.path.join(HERE, "card", "index.html")

LABEL = {
    "regime": "regime",
    "gamma_flip": "gamma flip",
    "walls_skew": "walls & skew",
    "vol_posture": "vol posture",
    "opex_stance": "opex stance",
    "fed_liquidity": "fed & liquidity",
    "crash_call": "base case",
}


def esc(s):
    return html.escape(str(s), quote=False)


def main():
    G = json.load(open(GAMMA, encoding="utf-8"))
    sig = json.load(open(SIG, encoding="utf-8"))

    spot = G["spot"]
    flip = G.get("gammaFlip")
    call_wall = G.get("callWall")
    put_wall = G.get("putWall")
    net = G.get("netTotal")
    unit = G.get("unit", "bn")
    regime = G.get("regime", "")
    asof = G.get("asofEt", "")

    lo = int(min(G["strikes"]) - 250)
    hi = int(max(G["strikes"]) + 250)
    span = hi - lo
    px = lambda v: round((v - lo) / span * 100, 2)

    def marker(v, cls):
        x = px(v)
        return ('<div class="mk %s" style="left:%s%%">'
                '<span class="tick"></span></div>') % (cls, x)

    ladder = []
    legend = []
    markers = []
    if put_wall:
        markers.append(("pw", put_wall, "put wall", f"{put_wall:,}"))
    if spot:
        markers.append(("spot", spot, "spot", f"{spot:,.0f}"))
    if flip is not None:
        markers.append(("flip", flip, "flip",
                        f"{flip:,.0f} · +{G.get('flipDistancePct', 0):.2f}%"))
    if call_wall:
        markers.append(("cw", call_wall, "call wall", f"{call_wall:,}"))
    for cls, v, label, sub in markers:
        ladder.append(marker(v, cls))
        legend.append('<div class="lg %s"><i></i><b>%s</b><span>%s</span></div>'
                      % (cls, esc(label), esc(sub)))

    # evidence strip (latest quote per theme, newest first)
    ev = []
    for k, label in LABEL.items():
        q = (sig.get(k) or {}).get("latest")
        if q:
            ev.append((q["date"], label, q["text"][:150]))
    ev.sort(key=lambda row: row[0], reverse=True)
    ev_html = "".join(
        '<div class="ev"><span class="d">%s</span><span class="lbl">%s</span>'
        '<span class="qt">“%s…”</span></div>'
        % (esc(d), esc(l), esc(t)) for d, l, t in ev[:5])

    page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Karsan signal card</title>
<style>
  :root {
    --bg: #0e1115; --ink: #e9e6e0; --ink2: #a7a49c; --ink3: #6f6d66;
    --hair: #262a31; --hair2: #333842;
    --pos: #3b86e0; --neg: #e34948; --gold: #d9a13b;
    --surf: #161a20;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--ink);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    font-size: 15px; line-height: 1.5; }
  .wrap { max-width: 1120px; margin: 0 auto; padding: 40px 24px 90px; }

  header { border-bottom: 1px solid var(--hair); padding-bottom: 20px; margin-bottom: 28px; }
  .eyebrow { font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ink3); margin-bottom: 8px; }
  h1 { font-size: 34px; font-weight: 750; letter-spacing: -0.03em; margin: 0 0 6px; }
  .sub { color: var(--ink2); font-size: 14px; margin: 0; }
  .sub b { color: var(--ink); }

  .grid { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(280px, 1fr); gap: 28px; }

  /* hero ladder */
  .hero { background: var(--surf); border: 1px solid var(--hair); padding: 24px 22px 28px; }
  .hero h2 { font-size: 13px; font-weight: 600; color: var(--ink2);
    margin: 0 0 4px; letter-spacing: 0.01em; }
  .hero .cap { font-size: 12.5px; color: var(--ink3); margin: 0 0 26px; }
  .ladder { position: relative; height: 150px; border-bottom: 1px solid var(--hair2); }
  .ladder .backdrop { position: absolute; top: 0; bottom: 0; background: var(--neg);
    opacity: 0.10; }
  .ladder::before { content: ""; position: absolute; left: 0; right: 0; top: 99px;
    height: 1px; background: var(--hair2); }
  .ruler { position: absolute; left: 0; right: 0; top: 112px;
    display: flex; justify-content: space-between; font-size: 11.5px;
    color: var(--ink3); font-variant-numeric: tabular-nums; }
  .mk { position: absolute; top: 8px; height: 106px; width: 2px;
    transform: translateX(-50%%); }
  .mk .tick { display: block; width: 2px; height: 100%%; }
  .mk.spot .tick { background: var(--ink); }
  .mk.flip .tick { background: var(--gold); }
  .mk.pw .tick { background: var(--neg); }
  .mk.cw .tick { background: var(--pos); }

  .legend { display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 8px; margin-top: 14px; }
  .lg { display: flex; align-items: baseline; gap: 8px;
    font-size: 12px; color: var(--ink2); }
  .lg i { width: 10px; height: 2px; flex: none; align-self: center; background: var(--ink3); }
  .lg.spot i { background: var(--ink); }
  .lg.flip i { background: var(--gold); }
  .lg.pw i { background: var(--neg); }
  .lg.cw i { background: var(--pos); }
  .lg b { font-weight: 650; color: var(--ink); font-size: 12.5px; }
  .lg span { color: var(--ink3); font-size: 11.5px; font-variant-numeric: tabular-nums; }
  .lg.flip b { color: var(--gold); }
  .lg.pw b { color: #f07574; }
  .lg.cw b { color: #6ea8ef; }
  .reveal { animation: draw 1.4s cubic-bezier(.2,.8,.2,1) both; }
  @keyframes draw { from { opacity: 0; transform: translateX(-50%%) scaleY(0); } }
  @media (prefers-reduced-motion: reduce) { .reveal { animation: none; } }

  /* stat rail */
  .stats { display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 1px; background: var(--hair); border: 1px solid var(--hair); margin-top: 26px; }
  .tile { background: var(--surf); padding: 14px 16px; }
  .tile .k { font-size: 11.5px; color: var(--ink3); margin-bottom: 4px; }
  .tile .v { font-size: 24px; font-weight: 700; letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums; }
  .tile .v.pos { color: var(--pos); } .tile .v.neg { color: var(--neg); }
  .tile .u { font-size: 12px; color: var(--ink3); font-weight: 400; margin-left: 4px; }
  .tile .note { font-size: 11.5px; color: var(--ink3); margin-top: 2px; }

  /* right rail */
  .rail { display: flex; flex-direction: column; gap: 22px; }
  .state { background: var(--surf); border: 1px solid var(--hair); padding: 18px; }
  .state h3 { font-size: 12px; font-weight: 650; color: var(--ink2); margin: 0 0 12px; }
  .state .row { display: flex; align-items: baseline; gap: 8px; padding: 7px 0;
    border-top: 1px solid var(--hair); font-size: 13.5px; }
  .state .row .k { color: var(--ink3); font-size: 12.5px; }
  .state .row .v { margin-left: auto; color: var(--ink); font-variant-numeric: tabular-nums; }
  .state .row .v.neg { color: #f07574; }
  .state .row .v.pos { color: #6ea8ef; }
  .state .row .v.gold { color: var(--gold); }
  .quote { font-size: 13px; color: var(--ink2); border-left: 2px solid var(--hair2);
    padding-left: 12px; margin-top: 12px; }
  .quote b { color: var(--ink); font-weight: 600; }

  .ev { padding: 10px 0; border-top: 1px solid var(--hair); font-size: 13px; }
  .ev .d { color: var(--gold); font-size: 11.5px; font-variant-numeric: tabular-nums; }
  .ev .lbl { color: var(--ink3); font-size: 11px; text-transform: uppercase;
    letter-spacing: 0.04em; margin-left: 8px; }
  .ev .qt { display: block; color: var(--ink2); margin-top: 3px; }

  footer { margin-top: 40px; border-top: 1px solid var(--hair); padding-top: 18px;
    font-size: 12.5px; color: var(--ink3); display: flex; gap: 18px; flex-wrap: wrap; }
  footer a { color: var(--ink2); text-decoration: none; border-bottom: 1px solid var(--hair2); }
  footer a:hover { color: var(--ink); }

  @media (max-width: 820px) {
    .grid { grid-template-columns: 1fr; }
    .stats { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="eyebrow">Dealer gamma · options desk</div>
    <h1>Karsan signal card</h1>
    <p class="sub">Chain as of <b>%s</b> · quotes verbatim from his last 30 days of interviews.</p>
  </header>

  <div class="grid">
    <div>
      <section class="hero">
        <h2>Where the levels sit</h2>
        <p class="cap">Short gamma below the flip amplifies moves; the walls bracket the range the market treats as its floor and ceiling.</p>
        <div class="ladder" id="ladder">
          <div class="backdrop" style="left:%s%%;right:%s%%"></div>
          %s
          <div class="ruler"><span>strike level</span><span>SPX</span></div>
        </div>
        <div class="legend">
          %s
        </div>
        <div class="stats">
          <div class="tile"><div class="k">Net gamma</div>
            <div class="v %s">%s<span class="u">%s</span></div>
            <div class="note">per 1%% move</div></div>
          <div class="tile"><div class="k">Gamma flip</div>
            <div class="v gold">%s</div>
            <div class="note">%s</div></div>
          <div class="tile"><div class="k">Regime</div>
            <div class="v %s">%s</div>
            <div class="note">%s</div></div>
        </div>
      </section>
    </div>

    <div class="rail">
      <section class="state">
        <h3>Current state</h3>
        <div class="row"><span class="k">Regime</span><span class="v %s">%s</span></div>
        <div class="row"><span class="k">Spot</span><span class="v">%s</span></div>
        <div class="row"><span class="k">Flip</span><span class="v gold">%s</span></div>
        <div class="row"><span class="k">Put wall</span><span class="v neg">%s</span></div>
        <div class="row"><span class="k">Call wall</span><span class="v pos">%s</span></div>
        <div class="quote"><b>%s</b> — “%s”</div>
      </section>

      <section class="state">
        <h3>Newest quotes</h3>
        %s
      </section>
    </div>
  </div>

  <footer>
    <span>View on the <a href="../karsan/" target="_blank">signal desk</a></span>
    <span>Hear it on <a href="../radio/" target="_blank">radio</a></span>
    <span>Read the <a href="../pajama/" target="_blank">pajama briefing</a></span>
    <span>Not investment advice · information only</span>
  </footer>
</div>

<script>
document.addEventListener("DOMContentLoaded", () => {
  const ladder = document.getElementById("ladder");
  [...ladder.querySelectorAll(".mk")].forEach((m, i) => {
    m.classList.add("reveal");
    m.style.animationDelay = (0.08 * i) + "s";
  });
});
</script>
</body>
</html>
""" % (esc(asof), px(put_wall or spot), 100 - px(call_wall or spot),
       "".join(ladder), "".join(legend),
       "neg" if (net or 0) < 0 else "pos", esc(net), esc(unit),
       esc(f"{flip:,.0f}" if flip is not None else "outside range"),
       esc(f"+{G.get('flipDistancePct', 0):.2f}% from spot"),
       "neg" if (net or 0) < 0 else "pos",
       esc("negative gamma" if (net or 0) < 0 else "positive gamma"),
       esc(regime),
       "neg" if (net or 0) < 0 else "pos", esc(regime),
       esc(f"{spot:,.0f}"), esc(f"{flip:,.0f}" if flip is not None else "—"),
       esc(f"{put_wall:,}" if put_wall else "—"),
       esc(f"{call_wall:,}" if call_wall else "—"),
       esc(LABEL.get(ev[0][1], ev[0][1]) if ev else ""),
       esc(ev[0][2] if ev else "no quotes this window"),
       ev_html)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("wrote", OUT, len(page), "bytes")


if __name__ == "__main__":
    main()
