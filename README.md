# interview-signal-desk

![The seven-stage pipeline ledger rendered as an interactive instrument page](docs/visual-readme.png)

The image above is the whole pipeline rendered as one instrument page. The served page is interactive, not a picture: a packet rides the ledger rail and pauses on hover, rows select on click, the arrow keys walk the stages, and the rail itself is draggable. Grab it, scrub through the stages, release, and the packet resumes from where you left it.

Open the interactive version: https://anthonycho-ux.github.io/interview-signal-desk/

Scripts that turn public interview transcripts into a signal desk: theme counts, stance labels, a signal card, a bilingual briefing, and a radio bulletin.

This project is built from public interviews with Cem Karsan. It is not affiliated with him or endorsed by him.

## Pipeline

![interview-signal-desk pipeline ledger: seven stages from public interview transcripts to signal card, pajama briefing, and radio bulletin, with committed byte sizes per stage](assets/pipeline-ledger.svg)

Each stage is a plain script you can run yourself; the exact commands are in [AGENTS.md](AGENTS.md).

See `AGENTS.md` for commands, conventions, and anti-patterns.

## Visual README

`docs/index.html` is the interactive page captured above. It is self-contained: no CDN, no external requests, system fonts only, light and dark schemes from `prefers-color-scheme` with a manual toggle.
