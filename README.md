# interview-signal-desk

![The seven-stage pipeline ledger rendered as an interactive instrument page](docs/visual-readme.png)

The image above is the whole pipeline rendered as one instrument page. The served page is interactive, not a picture: a packet rides the ledger rail and pauses on hover, rows select on click, the arrow keys walk the stages, and the rail itself is draggable. Grab it, scrub through the stages, release, and the packet resumes from where you left it.

Open the interactive version: https://anthonycho-ux.github.io/interview-signal-desk/

Scripts that turn public interview transcripts into a signal desk: theme counts, stance labels, a signal card, a bilingual briefing, and a radio bulletin.

This project is built from public interviews with Cem Karsan. It is not affiliated with him or endorsed by him.

## Pipeline

1. `fetch_inventory.py` -> `karsan-videos.json`
2. `normalize_transcripts.py` -> `transcripts.json` (reads `transcripts/*.en.vtt`, which is not committed)
3. `extract_signals.py` -> `signals.json`
4. `label_stance.py` -> `stance.json`
5. `build_signal_card.py` -> `card/index.html`
6. `generate-pajama-draft.py` -> `pajama-draft.txt`, then `build_pajama.py` -> `pajama/index.html`
7. `radio/radio_script.py` -> `radio/render_radio.py`

See `AGENTS.md` for commands, conventions, and anti-patterns.

## Visual README

`docs/index.html` is the interactive page captured above. It is self-contained: no CDN, no external requests, system fonts only, light and dark schemes from `prefers-color-scheme` with a manual toggle.
