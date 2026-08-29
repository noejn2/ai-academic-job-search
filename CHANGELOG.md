# Changelog

## 1.2.0

**Added**

- `/apply` Step 7 writes `START_HERE.txt` into every packet: where to apply, the
  vacancy number, the deadline, the exact filenames to upload with the posting's own
  label beside each, what is still blocking, and the portal quirks that decide
  whether the application counts as complete. A packet was verifiable but not
  actionable - `checklist.md` is written for this command's own use, and nothing in
  the folder told the user where to go. The upload list is read off the folder after
  Step 6 rather than from the Step 3 plan, so a filename in it always exists.

**Fixed**

- `/scrape` instructed the browser-header retry from an `allowed-tools` list holding
  neither `curl` nor a bare `Bash`, so the skill could not follow its own Step 3.
  Introduced in 1.1.0. `Bash(curl:*)` is a capability declaration on the skill, not
  an approval; `settings.json` still does not pre-approve it, so the retry prompts.
- Moving the gates ahead of the per-posting fetch in 1.1.0 left the appointment and
  language gates evaluating empty strings for exactly the records the fetch exists to
  fill - the AAEA board publishes no `description` and no `appointment` - and nothing
  re-gated afterwards. Step 3 now re-runs both on the filled record.
- Four contract-test classes added in 1.1.0 sat below `if __name__ == "__main__"`, so
  running the file directly executed 35 tests while `unittest discover` executed 52.
  CI uses discover and stayed green throughout. A test now pins the guard's position.
- The tracker-date contract test matched `submission date` against the whole of
  `outcome.md`, where the freeze paragraph also carries the phrase, so deleting the
  rule it exists to pin left the suite green. It now reads the tracker section only.

## 1.1.0

Restores safeguards that were lost when this workspace was cut down from
[MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search), found
by running both repositories side by side.

**Added**

- `tools/robots_check.py` and `09-web-research.md`, both ported back from upstream.
  1.0.0 dropped the `robots.txt` gate while keeping the browser-header retry the gate
  exists to authorise, which turned a documented exception into a standing
  instruction to spoof a user agent past a 403. The retry now runs only when the
  site's published policy allows the path, and it is written down in one file rather
  than copied into two command files that could drift apart.
- `/rank` Step 3b: an expiry sweep over already-ranked entries. Without it a closed
  search stayed on the shortlist forever, and this workspace keeps entries for 120
  days. Stored deadlines are parsed defensively; an absent or unparseable one is left
  alone rather than guessed at.
- `/outcome` freezes the packet into `submitted/` when a row moves to `applied`, and
  `/interview` prepares from that copy. `/interview` already promised to match what
  the committee read; nothing had been preserving it against a later re-draft.
- `tools/pdf_pages.py`, a standard-library page counter, wired into `/apply` Step 6
  and into CI. The LaTeX job asserted only that a PDF was non-empty, so a preamble
  change that pushed the shipped cover letter to two pages passed green while
  `06-cover-letter.md` still called one page a hard rule.
- `.gitignore` rules for images. An academic cover letter often carries a scanned
  signature and CVs in many countries carry a photograph.

**Fixed**

- `/scrape` runs its gates **before** the per-posting fetch, not after. Records the
  appointment, non-academic, country or language gate was about to drop were being
  fetched first, which on the AAEA board (no published descriptions) meant a request
  per posting on the board rather than per surviving posting.
- The country gate now says how to read `location`. JOE writes the country first
  (`UNITED STATES New Jersey Princeton`), EconJobMarket last (`New York, United
  States`); splitting on a comma silently dropped every JOE record.
- `/apply` stops when a posting cannot be retrieved instead of drafting from the
  title, which matters more here than upstream because `/rank` permits `title-only`
  scoring.
- `/rank` persists the `gate` reason it returns, as `/scrape` already did, and keeps
  the posting URL in the shortlist it tells the user to pass to `/apply`.
- `/outcome` sets the tracker `date` to the submission date when a row leaves
  `drafted`. It kept `/apply`'s draft date, so the "awaiting response past 30 days"
  count ran off a date the application was not sent on.
- `03-writing-style.md` is cleared by `/reset`. Its "Patterns observed in past
  applications" section is mined from the user's own letters, while `/reset` listed
  the file as holding no personal data. The test that should have caught this
  compared against a hardcoded tuple and searched the whole file; it now derives the
  list from `/setup` Step 7 and checks the reset block specifically.
- Two references to `/setup` "Path A" removed: this fork's `/setup` has no paths.
- `SECURITY.md` states that the permission allowlist governs Bash only, that
  `WebFetch`/`WebSearch` sit outside it, that the `curl` retry exists and is gated,
  and that instruction-level defenses are not a sandbox.
- `AGENTS.md` no longer carries a `framework_version` stamp; the mechanism that read
  it was removed in 1.0.0.

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
