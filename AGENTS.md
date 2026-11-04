# PROJECT KNOWLEDGE BASE

**Generated:** 2026-11-03 19:36 CST
**Commit:** 0efedbb
**Branch:** main

## OVERVIEW
Stdlib-only Python build scripts that turn Cem Karsan interview transcripts into static HTML pages (signal card, pajama briefing, radio bulletin) plus the signal desk pages. No requirements file, no tests, no CI. Data moves between scripts as JSON files in the repo root.

## STRUCTURE
```
./
├── fetch_inventory.py        # yt-dlp channel listing -> karsan-videos.json
├── normalize_transcripts.py  # transcripts/*.en.vtt -> transcripts.json
├── extract_signals.py        # transcripts.json -> signals.json (regex themes, wall levels)
├── label_stance.py           # signals.json -> stance.json (keyword prior, hand-correctable)
├── build_signal_card.py      # signals.json + gamma-terrain.json -> card/index.html
├── build_pajama.py           # pajama-draft.txt + signals.json -> pajama/index.html
├── generate-pajama-draft.py  # levels.json + signals.json -> pajama-draft.txt (Workers AI)
├── radio/                    # radio_script.py -> radio-script.json -> render_radio.py (ElevenLabs)
├── card/, pajama/            # generated HTML outputs
├── signal-desk.html          # desk page; no script in this repo writes it
├── deploy-desk/              # untracked Cloudflare workspace (node_modules, generated output)
├── transcripts/              # gitignored VTT input
└── *.json                    # data artifacts (signals, stance, gamma-terrain, karsan-videos)
```

## PIPELINE
1. `fetch_inventory.py` -> `karsan-videos.json`
2. `normalize_transcripts.py` (reads `karsan-videos.json` + VTT) -> `transcripts.json`
3. `extract_signals.py` -> `signals.json` (rewritten wholesale on each run)
4. `label_stance.py` -> `stance.json`
5. Builders read `signals.json`: `build_signal_card.py`, `generate-pajama-draft.py` -> `build_pajama.py`, `radio/radio_script.py` -> `radio/render_radio.py`

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Theme regexes | `extract_signals.py` RX, THEMES | proximity windows via DIST; wall levels need a numeric level near call/put/wall words |
| Stance sign convention | `label_stance.py` docstring | claim intensity, not bullish/bearish |
| Card layout, tabs, tooltips | `build_signal_card.py` main() | one ~600-line function that emits the HTML |
| Pajama EN/KR split | `build_pajama.py` lang_of, parse_draft | Hangul presence decides the language of each line |
| Radio script | `radio/radio_script.py` build() | numbers-only host lines plus verbatim quotes |
| Visual grammar | `VISUALIZATION-PRACTICE.md` | read before designing any new panel |
| Open work | `HANDOFF-2026-10-24.md` | ranked "what he emphasizes" panel, waiting on Anthony's go |

## CODE MAP
LSP unavailable (basedpyright not installed); symbols from grep, reference counts unmeasured.

| Symbol | Type | Location | Refs | Role |
|--------|------|----------|------|------|
| main | func | build_signal_card.py:104 | unmeasured | renders card HTML |
| build_wall | func | extract_signals.py:61 | unmeasured | wall level evidence |
| build | func | extract_signals.py:91 | unmeasured | theme regex matching |
| score | func | label_stance.py:57 | unmeasured | stance keyword score |
| parse_draft | func | build_pajama.py:51 | unmeasured | splits draft into bilingual sections |
| render | func | build_pajama.py:85 | unmeasured | writes pajama/index.html |
| call | func | generate-pajama-draft.py:55 | unmeasured | Workers AI request |
| parse_vtt | func | normalize_transcripts.py:40 | unmeasured | VTT cue parsing |
| fetch_channel | func | fetch_inventory.py:35 | unmeasured | yt-dlp channel fetch |
| build | func | radio/radio_script.py:49 | unmeasured | radio segments |
| pick_voice | func | radio/render_radio.py:67 | unmeasured | ElevenLabs voice selection |

## CONVENTIONS
- Paths resolve from `HERE = os.path.dirname(os.path.abspath(__file__))`; scripts run from any cwd and write next to themselves.
- Text files open with `encoding="utf-8"`; Korean text is first-class content. Exception: `generate-pajama-draft.py` reads `levels.json` and `signals.json` without it.
- Pipeline runs by hand, in order. No orchestrator, no Makefile.
- Corrections to stance labels live in `stance.json`, keyed `video:rounded_t`, so they survive a `signals.json` rebuild.

## ANTI-PATTERNS (THIS PROJECT)
- Do not hand-edit `signals.json`; `extract_signals.py` overwrites it.
- Do not add `transcripts.json` or `transcripts/` to git (both gitignored).
- Do not describe stance labels as bullish or bearish.
- Do not hardcode API keys. Scripts read the environment (see COMMANDS).
- Do not deploy or publish (the HANDOFF path copies to the deploy host) without Anthony's explicit approval.

## UNIQUE STYLES
- Ranked-ledger visual grammar: hairline rules, monospace numbers, one hue for magnitude (`VISUALIZATION-PRACTICE.md`).
- Pajama briefing is bilingual, EN and KR. A heading is a numbered line, or a line with `/` and no trailing period (`build_pajama.py` is_heading).

## COMMANDS
```bash
python3 fetch_inventory.py --days 30            # needs yt-dlp on PATH
python3 normalize_transcripts.py
python3 extract_signals.py
python3 label_stance.py
python3 build_signal_card.py                    # -> card/index.html
python3 generate-pajama-draft.py                # needs CLOUDFLARE_WORKERS_AI_TOKEN, CLOUDFLARE_ACCOUNT_ID
python3 build_pajama.py                         # -> pajama/index.html
python3 radio/radio_script.py                   # -> radio/radio-script.json
python3 radio/render_radio.py [--out DIR] [--voice VOICE_ID]   # needs ELEVENLABS_API_KEY or ~/.hermes/.env
```

## NOTES
- `levels.json` is absent at the repo root, so `generate-pajama-draft.py` cannot run as-is. A copy exists at `deploy-desk/public/levels.json`.
- `radio/radio_script.py` reads gamma data from `~/web/gamma/gamma-terrain.json`, not the repo copy. `build_signal_card.py` reads the repo's `gamma-terrain.json`.
- `render_radio.py` copies its outputs into `~/web/karsan/radio`.
- Working tree at generation: `build_pajama.py` modified; untracked `deploy-desk/` and `generate-pajama-draft.py`.
- `deploy-desk/` is not source. Skip it when searching for code.
- No deploy script exists in the repo; publishing is a manual copy.
