# Academic Job Search

A Claude Code workspace for running an academic job search end to end: find the
postings, score them against your record, and build the whole packet - CV, cover
letter, research and teaching statements, whatever else the posting names, and the
referee list.

It does **only** academic applications: positions hired by a university or college
department where the packet is a CV, statements and references. Tenure-track,
tenured, visiting, teaching-track, lecturer, postdoctoral, research professor. If you
also want industry, government or think-tank applications, use the general-purpose
template this one is derived from: <https://github.com/MadsLorentzen/ai-job-search>.

## What it does

| Command | Does |
|---|---|
| `/setup` | Reads your `documents/` folder, builds your profile, collects referees, assesses your research and teaching statements and reports their gaps |
| `/scrape` | Sweeps AEA JOE, EconJobMarket and the AAEA job board, plus `site:` searches for the boards without a fetcher; dedupes against what you have seen and applied to |
| `/rank` | Scores new postings - research fit 50%, teaching fit 30%, career alignment 20% - and returns a shortlist |
| `/apply` | Evaluates one posting in depth, then builds the packet: tailored CV, cover letter, tailored statements, any other required statement, referee list, archived posting and a required-documents checklist |
| `/outcome` | Records where each application stands: applied, interview, flyout, offer, closed |
| `/interview` | Builds a stage-specific prep pack - first-round questions, or a flyout plan covering the job talk, teaching demo and one-on-ones |
| `/reset` | Clears personal data back to the placeholders the template ships with |

## Requirements

- [Claude Code](https://claude.com/claude-code)
- A LaTeX distribution with `pdflatex` (TeX Live, MacTeX or MiKTeX)
- Python 3.10 or newer, standard library only. No packages to install, no Node, no
  API keys
- **Your own CV as a `.tex` file.** This workspace ships no CV template: an academic
  CV is a document you already maintain, and `/apply` tailors a copy of yours per
  posting

## Getting started

Click **Use this template** on <https://github.com/noejn2/ai-academic-job-search>
and create your own copy - **private**, since it will hold your record - then clone it:

```bash
git clone git@github.com:<you>/<your-copy>.git
cd <your-copy>
```

(Do not use the Fork button: a fork of a public repository cannot be made private.)

Put your materials in `documents/` - at minimum `documents/cv/your_cv.tex`, ideally
also your research and teaching statements in `documents/statements/` and a referee
list in `documents/references/`. See `documents/README.md` for the layout, and
`SETUP.md` for the full install, including the private-remote recipe.

Then, in Claude Code:

```
/setup      # build the profile from your documents
/scrape     # find postings
/rank       # score them
/apply <url or pasted posting>
```

## Your data stays yours

`documents/`, `applications/`, `job_search_tracker.csv` and the scrape state are
gitignored. The profile files under `.claude/skills/` **are** tracked and hold your
record once `/setup` runs - so work in a private clone, or keep those commits local.
`/setup` warns you before writing anything if your `origin` is public.
`tools/security_guards.py` fails the build if those ignore rules are ever weakened.

## How a packet is built

`/apply` writes one folder per posting:

```
applications/<institution>_<role>/
├── checklist.md            the posting's required documents, quoted, with status
├── job_posting.md          the posting text, archived verbatim
├── preamble.tex            shared by every .tex below, so the packet is one document
├── cv.tex / cv.pdf         your master CV, reordered and re-emphasised for this search
├── cover_letter.tex/.pdf   one page, or two when the posting requires it
├── research_statement.*    your master statement, tailored to this department
├── teaching_statement.*    same, and built around the courses the posting names
├── references.md           your referees, in the order the portal asks for
└── outcome.md              written later by /outcome
```

Everything compiles with `pdflatex` run twice. Nothing is invented: every claim
traces to your profile, your CV or your statements, and gaps are stated rather than
papered over. Reference letters are never drafted here - your referees send their own.

## Running the checks

```bash
python3 -m unittest discover -s tests -t .     # the test suite
uv run --with pyyaml python3 tools/lint_skills.py   # or: pip install pyyaml first
python3 tools/security_guards.py               # personal-data ignore rules intact
python3 tools/boards.py --board all --academic-only --format table   # live board check
```

## Credit

Derived from [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search),
MIT licensed. The pipeline shape, the drafter-reviewer workflow and the privacy
guards come from there; the academic packet, the board fetcher and the fit framework
are this fork's.
