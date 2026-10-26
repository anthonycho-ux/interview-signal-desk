# Visualization practice (adopted from the priority-stack mockup)

Anthony pointed at `priority-stack-gemini.jpg` and said he likes it because it follows the
visualization practice he is familiar with. That mockup is the reference register for ranked
market evidence in this project. Read it before designing a new panel.

## The grammar

1. **Ranked ledger, not cards.** One row per item, sorted by volume, rank number in its own
   narrow right-aligned column. A zero-volume item stays visible, dimmed, with dashes, never
   dropped.
2. **Hairline rules only.** One horizontal rule between rows, no vertical rules, no shadows,
   no rounded card per item. The table is a single bordered block with rounded outer corners.
3. **Uppercase labels, sentence-case everything else.** Theme names in uppercase with slight
   letter spacing. Status as a small uppercase word under the label, colored (green confirmed,
   gray unconfirmed, red rejected).
4. **Monospace for every number.** Counts, percentages, timestamps, quote text. Tabular
   figures so columns align. Sans for labels and prose.
5. **Proportional bar under the share, not beside it.** A 3px bar sitting under the percentage,
   width proportional to share, colored amber for the top two by volume and neutral for the
   rest. A visible track is optional; the fill alone reads cleaner.
6. **A paired evidence column.** The claim is never alone: the row carries a real quote in
   monospace with its source and timestamp, clickable to open the transcript at that moment.
7. **Provenance footer.** Data window, total counts, dimensions analyzed, and the legend for
   every color and bar in one line. If a number is provisional, the footer says so.
8. **One screen.** Seven rows plus header plus footer fit a laptop viewport. If they do not,
   cut chrome, not data.

## What it is not

No cards, no drop shadows, no icon decoration, no gradient fills, no pie charts, no
rainbow categorical palette. The color carries meaning (top two, status, stance) or it is
absent.

## Where it lives

`signal-desk.html` renders the signal board with this grammar (`.ledger`, `.lrow`, `.lhead`,
`.ledger-foot`). The board sits full width below the two-column rail and transcript, because
a six-column table needs the canvas. Below 700px of panel width the evidence column drops to
its own line rather than overflowing.
