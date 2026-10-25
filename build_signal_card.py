#!/usr/bin/env python3
"""Build the interactive Karsan signal card.

Same trader-grade visual as the static card, now with:
  - theme tabs (All + per-theme) that filter the quote strip and emphasize
    the markers that belong to the selected theme,
  - hover/click tooltips on the level markers,
  - evidence quotes rendered client-side from embedded, grounded data.
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

# marker key -> theme it evidences (or None)
MARKER_THEME = {
    "spot": None,
    "flip": "gamma_flip",
    "pw": "walls_skew",
    "cw": "walls_skew",
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

    markers = []
    ladder = []
    legend = []
    if put_wall:
        markers.append({"key": "pw", "cls": "pw", "v": put_wall, "label": "put wall", "val": f"{put_wall:,}"})
    if spot:
        markers.append({"key": "spot", "cls": "spot", "v": spot, "label": "spot", "val": f"{spot:,.0f}"})
    if flip is not None:
        markers.append({"key": "flip", "cls": "flip", "v": flip, "label": "flip",
                        "val": f"{flip:,.0f} · +{G.get('flipDistancePct', 0):.2f}%"})
    if call_wall:
        markers.append({"key": "cw", "cls": "cw", "v": call_wall, "label": "call wall", "val": f"{call_wall:,}"})

    for m in markers:
        m["theme"] = MARKER_THEME.get(m["key"])
        ladder.append('<div class="mk %s" data-m="%s" style="left:%s%%">'
                      '<span class="tick"></span></div>'
                      % (m["cls"], m["key"], px(m["v"])))
    for m in markers:
        legend.append('<button class="lg %s" data-m="%s"><i></i>'
                      '<b>%s</b><span>%s</span></button>'
                      % (m["cls"], m["key"], esc(m["label"]), esc(m["val"])))

    # embed per-theme quotes for the client
    quotes_by_theme = {}
    for k, label in LABEL.items():
        qs = (sig.get(k) or {}).get("quotes") or []
        quotes_by_theme[k] = [
            {"date": q["date"], "key": k, "label": label, "text": q["text"][:180]}
            for q in qs[:4]
        ]
    data_json = json.dumps({
        "markers": markers,
        "themeLabel": LABEL,
        "themes": quotes_by_theme,
    }, ensure_ascii=False)

    page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Karsan signal card — interactive</title>
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

  header { border-bottom: 1px solid var(--hair); padding-bottom: 20px; margin-bottom: 26px; }
  .hdr { display: flex; align-items: flex-start; gap: 20px; }
  .langsw { margin-left: auto; display: inline-flex; border: 1px solid var(--hair);
    border-radius: 8px; overflow: hidden; font-size: 12.5px; flex: none; }
  .langsw button { font: inherit; border: 0; background: transparent;
    color: var(--ink2); padding: 5px 14px; cursor: pointer; }
  .langsw button.on { background: var(--ink2); color: var(--bg); }
  .eyebrow { font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ink3); margin-bottom: 8px; }
  h1 { font-size: 34px; font-weight: 750; letter-spacing: -0.03em; margin: 0 0 6px; }
  .sub { color: var(--ink2); font-size: 14px; margin: 0; }
  .sub b { color: var(--ink); }

  .grid { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(280px, 1fr); gap: 28px; }

  .hero { background: var(--surf); border: 1px solid var(--hair); padding: 24px 22px 24px; }
  .hero h2 { font-size: 13px; font-weight: 600; color: var(--ink2);
    margin: 0 0 4px; letter-spacing: 0.01em; }
  .hero .cap { font-size: 12.5px; color: var(--ink3); margin: 0 0 24px; }
  .ladder { position: relative; height: 150px; border-bottom: 1px solid var(--hair2); }
  .ladder .backdrop { position: absolute; top: 0; bottom: 0; background: var(--neg);
    opacity: 0.10; }
  .ladder::before { content: ""; position: absolute; left: 0; right: 0; top: 99px;
    height: 1px; background: var(--hair2); }
  .ruler { position: absolute; left: 0; right: 0; top: 112px;
    display: flex; justify-content: space-between; font-size: 11.5px;
    color: var(--ink3); font-variant-numeric: tabular-nums; }

  .mk { position: absolute; top: 8px; height: 106px; width: 2px;
    transform: translateX(-50%%); cursor: pointer; transition: filter 160ms; }
  .mk .tick { display: block; width: 2px; height: 100%%; }
  .mk.spot .tick { background: var(--ink); }
  .mk.flip .tick { background: var(--gold); }
  .mk.pw .tick { background: var(--neg); }
  .mk.cw .tick { background: var(--pos); }
  .ladder.dim .mk { opacity: 0.22; }
  .ladder.dim .mk.lit { opacity: 1; }

  .tip { position: absolute; z-index: 5; pointer-events: none; opacity: 0;
    background: #1c2128; border: 1px solid var(--hair2); padding: 8px 10px;
    font-size: 12.5px; color: var(--ink2); min-width: 170px; transition: opacity 90ms; }
  .tip.on { opacity: 1; }
  .tip b { display: block; color: var(--ink); font-size: 13px; margin-bottom: 2px; }

  .legend { display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 8px; margin-top: 14px; }
  .lg { display: flex; align-items: baseline; gap: 8px; text-align: left;
    background: transparent; border: 1px solid transparent; border-radius: 6px;
    padding: 6px 8px; cursor: pointer; font: inherit; color: var(--ink2); }
  .lg:hover { border-color: var(--hair2); }
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

  .stats { display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 1px; background: var(--hair); border: 1px solid var(--hair); margin-top: 24px; }
  .tile { background: var(--surf); padding: 14px 16px; }
  .tile .k { font-size: 11.5px; color: var(--ink3); margin-bottom: 4px; }
  .tile .v { font-size: 24px; font-weight: 700; letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums; }
  .tile .v.pos { color: var(--pos); } .tile .v.neg { color: var(--neg); }
  .tile .u { font-size: 12px; color: var(--ink3); font-weight: 400; margin-left: 4px; }
  .tile .note { font-size: 11.5px; color: var(--ink3); margin-top: 2px; }

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

  .tabs { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; }
  .tabs button { font: inherit; font-size: 12px; color: var(--ink2);
    background: transparent; border: 1px solid var(--hair); border-radius: 999px;
    padding: 4px 12px; cursor: pointer; }
  .tabs button:hover { border-color: var(--hair2); }
  .tabs button.on { color: var(--ink); border-color: var(--ink2); }

  .ev { padding: 10px 0; border-top: 1px solid var(--hair); font-size: 13px; }
  .ev .d { color: var(--gold); font-size: 11.5px; font-variant-numeric: tabular-nums; }
  .ev .lbl { color: var(--ink3); font-size: 11px; text-transform: uppercase;
    letter-spacing: 0.04em; margin-left: 8px; }
  .ev .qt { display: block; color: var(--ink2); margin-top: 3px; }
  .ev.off { opacity: 0.45; }

  footer { margin-top: 40px; border-top: 1px solid var(--hair); padding-top: 18px;
    font-size: 12.5px; color: var(--ink3); display: flex; gap: 18px; flex-wrap: wrap; }
  footer a { color: var(--ink2); text-decoration: none; border-bottom: 1px solid var(--hair2); }
  footer a:hover { color: var(--ink); }

  @media (max-width: 820px) {
    .grid { grid-template-columns: 1fr; }
    .stats { grid-template-columns: 1fr; }
    .legend { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="hdr">
      <div>
        <div class="eyebrow" data-i18n="eyebrow">Dealer gamma · options desk</div>
        <h1 data-i18n="title">Karsan signal card</h1>
        <p class="sub"><span data-i18n="subA">Chain as of</span> <b>%s</b>
          <span data-i18n="subB">· interactive — pick a theme to filter the evidence, click a level for more.</span></p>
      </div>
      <div class="langsw" id="langsw">
        <button data-l="en" class="on">EN</button>
        <button data-l="kr">KR</button>
      </div>
    </div>
  </header>

  <div class="grid">
    <div>
      <section class="hero">
        <h2 data-i18n="heroH">Where the levels sit</h2>
        <p class="cap" data-i18n="heroCap">Short gamma below the flip amplifies moves; the walls bracket the floor and ceiling. Hover or click a level.</p>
        <div class="ladder" id="ladder">
          <div class="backdrop" style="left:%s%%;right:%s%%"></div>
          %s
          <div class="ruler"><span>strike level</span><span>SPX</span></div>
          <div class="tip" id="tip"></div>
        </div>
        <div class="legend" id="legend">
          %s
        </div>
        <div class="stats">
          <div class="tile"><div class="k" data-i18n="statNet">Net gamma</div>
            <div class="v %s">%s<span class="u">%s</span></div>
            <div class="note" data-i18n="statPer">per 1%% move</div></div>
          <div class="tile"><div class="k" data-i18n="statFlip">Gamma flip</div>
            <div class="v gold">%s</div>
            <div class="note"><span data-i18n="statDistPre"></span><b>%s</b>
              <span data-i18n="statDistPost">from spot</span></div></div>
          <div class="tile"><div class="k" data-i18n="statRegime">Regime</div>
            <div class="v %s">%s</div>
            %s</div>
        </div>
      </section>
    </div>

    <div class="rail">
      <section class="state">
        <h3 data-i18n="stateH">Current state</h3>
        <div class="row"><span class="k" data-i18n="stateRegime">Regime</span><span class="v %s">%s</span></div>
        <div class="row"><span class="k" data-i18n="stateSpot">Spot</span><span class="v">%s</span></div>
        <div class="row"><span class="k" data-i18n="stateFlip">Flip</span><span class="v gold">%s</span></div>
        <div class="row"><span class="k" data-i18n="statePW">Put wall</span><span class="v neg">%s</span></div>
        <div class="row"><span class="k" data-i18n="stateCW">Call wall</span><span class="v pos">%s</span></div>
        <div class="quote"><b>%s</b> — “%s”</div>
      </section>

      <section class="state">
        <h3 data-i18n="evH">Evidence by theme</h3>
        <div class="tabs" id="tabs"></div>
        <div id="quotes"></div>
      </section>
    </div>
  </div>

  <footer>
    <span data-i18n-html="footDesk">View on the <a href="../karsan/" target="_blank">signal desk</a></span>
    <span data-i18n-html="footRadio">Hear it on <a href="../radio/" target="_blank">radio</a></span>
    <span data-i18n-html="footPajama">Read the <a href="../pajama/" target="_blank">pajama briefing</a></span>
    <span data-i18n="footFine">Not investment advice · information only</span>
  </footer>
</div>

<script>
const CARD = %s;

const I18N = {
  en: {
    eyebrow: "Dealer gamma · options desk",
    title: "Karsan signal card",
    subA: "Chain as of",
    subB: "· interactive — pick a theme to filter the evidence, click a level for more.",
    heroH: "Where the levels sit",
    heroCap: "Short gamma below the flip amplifies moves; the walls bracket the floor and ceiling. Hover or click a level.",
    statNet: "Net gamma",
    statPer: "per 1%% move",
    statFlip: "Gamma flip",
    statDistPre: "",
    statDistPost: "from spot",
    statRegime: "Regime",
    statNeg: "negative gamma",
    statPos: "positive gamma",
    stateH: "Current state",
    stateRegime: "Regime",
    stateSpot: "Spot",
    stateFlip: "Flip",
    statePW: "Put wall",
    stateCW: "Call wall",
    evH: "Evidence by theme",
    evEmpty: "No explicit mention in this 30-day window.",
    tipAxis: "SPX level on the strike axis",
    footDesk: 'View on the <a href="../karsan/" target="_blank">signal desk</a>',
    footRadio: 'Hear it on <a href="../radio/" target="_blank">radio</a>',
    footPajama: 'Read the <a href="../pajama/" target="_blank">pajama briefing</a>',
    footFine: "Not investment advice · information only",
    all: "All"
  },
  kr: {
    eyebrow: "옵션 데스크 · Dealer gamma",
    title: "Karsan signal card",
    subA: "체인 기준",
    subB: "· 인터랙티브 — 테마를 골라 근거를 필터링하고, 레벨을 클릭해 자세히 보세요.",
    heroH: "레벨 위치",
    heroCap: "플립 아래 short gamma는 움직임을 증폭하고, walls는 바닥과 천장을 받칩니다. 레벨에 마우스를 올리거나 클릭하세요.",
    statNet: "Net gamma",
    statPer: "1%% 움직임당",
    statFlip: "Gamma flip",
    statDistPre: "",
    statDistPost: "from spot",
    statRegime: "Regime",
    statNeg: "negative gamma",
    statPos: "positive gamma",
    stateH: "현재 상태",
    stateRegime: "Regime",
    stateSpot: "Spot",
    stateFlip: "Flip",
    statePW: "Put wall",
    stateCW: "Call wall",
    evH: "테마별 근거",
    evEmpty: "이 30일 창에서 직접 언급 없음.",
    tipAxis: "strike 축의 SPX level",
    footDesk: '시그널 <a href="../karsan/" target="_blank">데스크</a> 보기',
    footRadio: '<a href="../radio/" target="_blank">라디오</a>로 듣기',
    footPajama: '<a href="../pajama/" target="_blank">파자마 브리핑</a> 읽기',
    footFine: "투자 조언 아님 · 정보 제공용",
    all: "전체"
  }
};

const THEME_KR = {
  regime: "Regime",
  gamma_flip: "Gamma flip",
  walls_skew: "Walls & skew",
  vol_posture: "Vol posture",
  opex_stance: "Opex stance",
  fed_liquidity: "Fed & liquidity",
  crash_call: "Base case"
};

const MARKER_NAMES = {
  pw: ["put wall", "put wall"],
  spot: ["spot", "spot"],
  flip: ["flip", "flip"],
  cw: ["call wall", "call wall"]
};

(() => {
  const ladder = document.getElementById("ladder");
  const legend = document.getElementById("legend");
  const tabs = document.getElementById("tabs");
  const quotes = document.getElementById("quotes");
  const tip = document.getElementById("tip");
  const langsw = document.getElementById("langsw");
  const themeKeys = Object.keys(CARD.themes);
  let theme = "all";
  let lang = "en";
  try { const s = localStorage.getItem("card-lang"); if (s === "kr" || s === "en") lang = s; } catch (e) {}

  function t(key) { return (I18N[lang] && I18N[lang][key]) || ""; }

  /* language toggle (KR/EN) */
  function applyLang() {
    document.querySelectorAll("[data-i18n]").forEach(el => {
      el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll("[data-i18n-html]").forEach(el => {
      el.innerHTML = t(el.dataset.i18nHtml);
    });
    [...langsw.children].forEach(b => b.classList.toggle("on", b.dataset.l === lang));
    renderTabs();
    renderLegend();
    renderQuotes();
    try { localStorage.setItem("card-lang", lang); } catch (e) {}
  }
  langsw.addEventListener("click", e => {
    const b = e.target.closest("button");
    if (!b) return;
    lang = b.dataset.l;
    applyLang();
  });

  /* tabs */
  function renderTabs() {
    const tabNames = [["all", t("all")]].concat(themeKeys.map(k =>
      [k, lang === "kr" ? (THEME_KR[k] || CARD.themeLabel[k]) : CARD.themeLabel[k]]
    ));
    tabs.innerHTML = tabNames.map(([k, name]) =>
      '<button data-t="' + k + '"' + (k === theme ? ' class="on"' : "") + ">" + name + "</button>"
    ).join("");
  }
  tabs.addEventListener("click", e => {
    const b = e.target.closest("button");
    if (!b) return;
    theme = b.dataset.t;
    [...tabs.children].forEach(x => x.classList.toggle("on", x === b));
    renderQuotes();
    renderLadder();
  });

  function renderQuotes() {
    const list = [];
    if (theme === "all") {
      for (const k of themeKeys) list.push(...CARD.themes[k]);
      list.sort((a, b) => b.date.localeCompare(a.date));
    } else {
      list.push(...CARD.themes[theme]);
    }
    if (!list.length) {
      quotes.innerHTML = '<div class="ev"><span class="qt">' + t("evEmpty") + "</span></div>";
      return;
    }
    quotes.innerHTML = list.map(q =>
      '<div class="ev"><span class="d">' + q.date + '</span><span class="lbl">' +
      (lang === "kr" ? (THEME_KR[q.key] || q.label) : q.label) +
      '</span><span class="qt">“' + q.text + '…”</span></div>'
    ).join("");
  }

  function renderLegend() {
    [...legend.querySelectorAll(".lg")].forEach(b => {
      const nm = MARKER_NAMES[b.dataset.m] || [];
      const label = lang === "kr" ? (nm[1] || "") : (nm[0] || "");
      if (label) b.querySelector("b").textContent = label;
    });
  }

  function renderLadder() {
    const any = theme !== "all";
    ladder.classList.toggle("dim", any);
    [...ladder.querySelectorAll(".mk")].forEach(m => {
      const t = CARD.markers.find(x => x.key === m.dataset.m);
      const lit = !any || (t && t.theme === theme);
      m.classList.toggle("lit", lit);
    });
  }

  /* marker tooltips + legend focus */
  function showTip(m, ev) {
    const d = CARD.markers.find(x => x.key === m.dataset.m);
    if (!d) return;
    const nm = MARKER_NAMES[d.key] || [];
    const label = lang === "kr" ? (nm[1] || d.label) : (nm[0] || d.label);
    tip.innerHTML = '<b>' + label + " · " + d.val + "</b>" + t("tipAxis");
    const r = ladder.getBoundingClientRect();
    const mx = ev.clientX - r.left, my = ev.clientY - r.top;
    tip.style.left = Math.min(Math.max(8, mx - 85), r.width - 180) + "px";
    tip.style.top = (my - 52) + "px";
    tip.classList.add("on");
  }
  ladder.addEventListener("pointermove", e => {
    const m = e.target.closest(".mk");
    if (m) showTip(m, e); else tip.classList.remove("on");
  });
  ladder.addEventListener("pointerleave", () => tip.classList.remove("on"));
  legend.addEventListener("click", e => {
    const b = e.target.closest(".lg");
    if (!b) return;
    const m = [...ladder.querySelectorAll(".mk")].find(x => x.dataset.m === b.dataset.m);
    if (m) { m.scrollIntoView({ block: "nearest" }); m.classList.add("lit"); }
  });

  applyLang();
})();
</script>
</body>
</html>
""" % (esc(asof), px(put_wall or spot), 100 - px(call_wall or spot),
       "".join(ladder), "".join(legend),
       "neg" if (net or 0) < 0 else "pos", esc(net), esc(unit),
       esc(f"{flip:,.0f}" if flip is not None else "outside range"),
       esc(f"+{G.get('flipDistancePct', 0):.2f}%"),
       "neg" if (net or 0) < 0 else "pos",
       ('<div class="note" data-i18n="statNeg">negative gamma</div>'
        if (net or 0) < 0 else
        '<div class="note" data-i18n="statPos">positive gamma</div>'),
       esc(regime),
       "neg" if (net or 0) < 0 else "pos", esc(regime),
       esc(f"{spot:,.0f}"), esc(f"{flip:,.0f}" if flip is not None else "—"),
       esc(f"{put_wall:,}" if put_wall else "—"),
       esc(f"{call_wall:,}" if call_wall else "—"),
       esc(LABEL.get((sig.get("fed_liquidity") or {}).get("latest", {}).get("video", ""), "fed & liquidity") if (sig.get("fed_liquidity") or {}).get("latest") else ""),
       esc((sig.get("fed_liquidity") or {}).get("latest", {}).get("text", "")[:120] if (sig.get("fed_liquidity") or {}).get("latest") else "no quotes this window"),
       data_json)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("wrote", OUT, len(page), "bytes")


if __name__ == "__main__":
    main()
