# Changelog

## 1.0.0

First release. An academic-only workspace derived from
[MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search).

**Added**

- `tools/boards.py`: standard-library fetcher for AEA JOE (via the board's own
  spreadsheet export, so postings arrive with full text and deadlines),
  EconJobMarket and the AAEA job board.
- `08-statements.md`: assessment of the user's research and teaching statements,
  with the sources staying in `documents/statements/`.
- Referee collection in `/setup`, with a three-referee minimum before the profile
  counts as complete.
- Per-posting packet folders holding the whole application, including a
  `checklist.md` quoting the posting's required documents.
- `templates/`: shared LaTeX preamble plus statement and cover-letter skeletons,
  all `pdflatex`.
- `documents/statements/`, `documents/papers/` and `documents/teaching/`.

**Changed**

- Fit framework: research 50%, teaching 30%, career alignment 20%, with appointment
  type, eligibility, country and language as gates. Salary and behavioural scoring
  dimensions removed.
- Tracker status vocabulary follows an academic search: drafted, applied, interview,
  flyout, offer, then hired, rejected, no_response, offer_declined, withdrawn.
- `/interview` prepares a first-round interview or a flyout, including the job talk
  and teaching demonstration.
- The CV is the user's own `.tex` file; no CV template ships and no page limit is
  applied.
- The cover letter is a plain `article`-class letter sharing the packet preamble,
  one page by default and two when the posting requires it.

**Removed**

- The industry track in its entirety: two-page CV rule, ATS and keyword extraction,
  moderncv and `cover.cls` templates, salary lookup and its data tooling.
- `/gmail-sync`, `/notion-sync`, `/html-report`, `/upskill`, `/expand`,
  `/add-portal`, `/add-template`, and the portal CLIs under `.agents/` with their
  Node/bun toolchain.
- Upstream-sync tooling and the framework-version CI gate.
