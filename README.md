# interview-signal-desk

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
