<!-- SETUP: /setup writes this file. Replace every [BRACKETED] token. -->

# Search Configuration

What `/scrape` searches for. `/setup --section search` rewrites it; edit it by hand
any time your priorities change.

---

## Appointment types in scope

`/scrape`'s appointment gate keeps these and drops the rest. Delete the lines you do
not want.

- [x] Tenure-track (assistant professor)
- [x] Tenured (associate / full professor)
- [ ] Teaching-track / lecturer / instructor
- [ ] Visiting (visiting assistant professor, visiting scholar)
- [ ] Postdoctoral
- [ ] Research professor / research scientist at a university

Always out of scope, whatever is ticked above: pre-doctoral and research-assistant
posts, and every position not hired by a university or college department
(industry, government agencies, national labs, think tanks, NGOs).

---

## Field terms

Passed to `tools/boards.py` as `--query` arguments, OR-ed against the whole record.
Keep them short: a board's own keywords are terse.

- Primary field: `[YOUR_FIELD]`
- Subfields: `[SUBFIELD_1]`, `[SUBFIELD_2]`, `[SUBFIELD_3]`
- Methods that show up in postings: `[METHOD_1]`, `[METHOD_2]`

---

## Countries in scope

- `[COUNTRY_1]`
- `[COUNTRY_2]`

Relocation is assumed. There is no commute radius in an academic search.

---

## Boards with a fetcher

Read by `python3 tools/boards.py --board all --academic-only`. No account, no key.

| Board | What it covers |
|---|---|
| **AEA JOE** (`aeaweb.org/joe`) | The economics market. Read through the board's spreadsheet export, so each record arrives with the full posting text, the deadline and the section label. |
| **EconJobMarket** (`econjobmarket.org/positions`) | Economics, overlapping JOE but not identical; carries European and Canadian searches JOE misses. |
| **AAEA Job Board** (`aaea.execinc.com/edibo/JobBoard`) | Agricultural and applied economics specifically. No deadlines published; titles and institutions only, so `/scrape` fetches each posting page. |

Outside economics, these three return little. Add your field's board as a
`site:` query below rather than writing a parser: the fetcher exists because these
three publish structured data, not because parsing is the goal.

---

## Search sites without a fetcher

`/scrape` Step 1b runs these as WebSearch queries every sweep.

```
site:higheredjobs.com "[YOUR_FIELD]" assistant professor
site:academicjobsonline.org [YOUR_FIELD]
site:jobs.chronicle.com [YOUR_FIELD] faculty
site:apply.interfolio.com [YOUR_FIELD] assistant professor
"[SUBFIELD_1]" "assistant professor" [CURRENT_SEASON] site:.edu
"[YOUR_FIELD]" "visiting assistant professor" site:.edu
```

Add one line per department you are watching directly, e.g.
`site:careers.[UNIVERSITY].edu [YOUR_FIELD]`.

---

## Filters applied after the search

- **Deadline:** postings whose deadline has passed are stored as expired, never shown as new.
- **Language:** a posting stating a required working language absent from your profile is skipped.
- **Recency:** postings first seen more than 120 days ago and never applied to are dropped from the report; academic searches run long, so this window is much wider than an industry one.
