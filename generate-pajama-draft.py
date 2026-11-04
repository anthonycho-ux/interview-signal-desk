#!/usr/bin/env python3
"""Generate today's pajama-trader briefing draft from desk data via Gemma 4.

Output: pajama-draft-YYYYMMDD.txt (standalone archive)
         pajama-draft.txt (the file build_pajama.py consumes)
Replaces the old hand-written Gemini draft. Run after the desk refresh.

Exit 0 only when the draft was regenerated from today's data.
"""
import json, os, re, sys, time, urllib.request

TOKEN = os.environ.get("CLOUDFLARE_WORKERS_AI_TOKEN", "")
ACCT = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
if not TOKEN or not ACCT:
    print("missing Workers AI token/account", file=sys.stderr); sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
LEVELS = os.path.join(HERE, "levels.json")
SIG = os.path.join(HERE, "signals.json")
OUT = os.path.join(HERE, "pajama-draft.txt")

BASE = f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/ai/run/@cf/google/gemma-4-26b-a4b-it"

SYS = """
You are a Korean financial market analyst writing for individual retail traders (pajama traders).
Voice: Cha Mu-sik. Blunt, experienced, plain, concrete, a little dry. Korean is the primary voice.

Output format (STRICT, no markdown, no asterisks, no hashes):
1. The headline read / 헤드라인
<one English sentence>
<one Korean sentence>

2. Market structure / 시장 구조
<English paragraph>
<Korean paragraph>

3. The evidence / 근거
<English paragraph citing the quotes>
<Korean paragraph>

4. What to watch / 체크포인트
<English paragraph>
<Korean paragraph>

5. Bottom line / 결론
<English paragraph>
<Korean paragraph>

Rules:
- Lead with the gamma flip number. Keep flip, put wall, gamma in English inside Korean prose.
- Use only the data provided. Never invent numbers.
- Every section heading must be exactly like: 1. English title / 한국어 제목
"""

def call(text, n=3):
    body = json.dumps({"messages":[{"role":"system","content":SYS},{"role":"user","content":text}],
                       "chat_template_kwargs":{"enable_thinking":False}}).encode()
    req = urllib.request.Request(BASE, data=body, headers={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"})
    for i in range(n):
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=120).read())
            c = d["result"]["choices"][0]["message"]["content"].strip()
            if c: return c
        except Exception as e:
            print(f"  attempt {i+1}: {e}", file=sys.stderr)
            if i < n-1: time.sleep(8*(i+1))
    return None

def strip_md(t):
    t = re.sub(r"\*{1,2}", "", t)
    t = re.sub(r"^#+\s*", "", t, flags=re.M)
    return t

def main():
    levels = json.load(open(LEVELS))
    sig = json.load(open(SIG))
    # evidence for the context: latest quote per theme
    ctx = []
    for k, t in sig.items():
        qs = t.get("quotes") or []
        if qs:
            ctx.append(f"{k} ({qs[-1].get('date','')}): {qs[-1]['text'][:180]}")
    levels_ctx = {
        "asof": levels.get("asof"),
        "spot": levels.get("spot"),
        "flip": levels.get("flip"),
        "net_gamma_at_spot_bn": levels.get("net_gamma_at_spot_bn"),
    }
    if any(v is None for v in levels_ctx.values()):
        print("levels.json missing core fields", file=sys.stderr); sys.exit(1)

    prompt = f"""Write today's pajama-trader briefing.

Market data:
- asof: {levels_ctx['asof']}
- spot: {levels_ctx['spot']}
- gamma flip: {levels_ctx['flip']}
- net gamma at spot: {levels_ctx['net_gamma_at_spot_bn']}B

Theme evidence (Karsan quotes):
{chr(10).join(ctx)}

Write the briefing now."""

    draft = call(prompt)
    if not draft:
        print("generation failed after retries", file=sys.stderr); sys.exit(1)

    draft = strip_md(draft)
    open(OUT, "w", encoding="utf-8").write(draft)
    stamp = __import__("datetime").date.today().strftime("%Y%m%d")
    with open(os.path.join(HERE, f"pajama-draft-{stamp}.txt"), "w", encoding="utf-8") as f:
        f.write(draft)
    print(f"ok: {len(draft)} chars -> pajama-draft.txt (+{stamp})")

main()
