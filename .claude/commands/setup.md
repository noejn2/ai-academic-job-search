# /setup - Profile Onboarding

You are building the candidate profile this workspace runs on, from the documents in
`documents/`. The user supplies the materials; you read them, extract what is there,
ask only for what is missing, and write the profile files.

`$ARGUMENTS` may contain `--section <name>` where name is `profile`, `referees`,
`statements`, `search` or `cv`. Run only that section and stop.

Follow the steps in order.

---

## Step 0: Privacy check

Run `git remote get-url origin`. If it fails, continue silently.

If there is a GitHub `origin`, check it with `gh repo view <owner/repo> --json
visibility,isFork` when `gh` is available. If the origin is a **public** repository
or its visibility cannot be determined, stop and warn before writing anything:

> **Before we start:** your `origin` points at `<owner/repo>`, which is public. This
> setup writes your name, contact details, publication record and referees into
> tracked files. Your `documents/`, packets and tracker are gitignored, but the
> profile files are not. Two safe options: keep these commits local and never push
> them, or push to a **private** repository - `SETUP.md` section 6 has the recipe.
> Continue?

Wait for the answer. A private origin or no origin needs no warning.

---

## Step 1: Inventory `documents/`

Glob `documents/**/*` and print what is there:

```
## Documents found

**cv/**            [files, or "(empty) - required"]
**statements/**    [files, or "(empty)"]
**papers/**        [files, or "(empty)"]
**references/**    [files, or "(empty)"]
**teaching/**      [files, or "(empty)"]
**diplomas/**      [files, or "(empty)"]
```

**A `.tex` CV in `documents/cv/` is required.** Without it, stop and say so: this
workspace tailors your own CV per posting and ships no template, so there is nothing
to work from. A PDF is not enough - a PDF cannot be tailored. Point at
`documents/README.md`.

`.rtf` files are readable: convert with `textutil -convert txt -stdout <file>` on
macOS, otherwise ask the user to save as `.txt` or `.md`.

If `documents/` holds everything except statements, continue - statements are
collected in Step 4 and their absence is reported as a gap, not a blocker.

---

## Step 2: Read and extract

Read the profile files first so the merge is informed, then the documents.

Profile files: `01-candidate-profile.md`, `02-behavioral-profile.md`,
`03-writing-style.md`, `04-job-evaluation.md`, `07-interview-prep.md`,
`08-statements.md`.

Then, from `documents/`:

- **`cv/`** - name, contact, education (degree, institution, years, dissertation,
  advisor), appointments, publications split by category (peer-reviewed, chapters,
  under review, working papers, in preparation), grants with role and amount, awards,
  teaching with course codes and enrolments, service, presentations, software, and
  the CV's own References section.
- **`teaching/`** - syllabi, evaluation reports. Record scores **verbatim**; never
  estimate or average across courses that were not averaged.
- **`papers/`** - titles and status of the job market paper and writing samples.
- **`references/`** - referee names, titles, institutions, emails, relationships. A
  letter kept here is read for the competency language it uses, which feeds
  `02-behavioral-profile.md`. Never treat a letter as something to reproduce.
- **`diplomas/`** - official degree titles, institutions, dates.
- **`applications/*/outcome.md`** - past results, for the calibration section of
  `04-job-evaluation.md`. Skip applications still in progress.

Cross-reference the documents against each other. If dates, titles or degree names
disagree, list the conflicts and ask which is correct before writing. Never resolve a
conflict yourself.

---

## Step 3: Referees

Read the referees already in `01-candidate-profile.md`, the CV's References section
and anything in `documents/references/`. Present what you found, then ask for what is
missing.

Per referee: **name, title, institution, email, phone (optional), relationship.**

- **Minimum three.** With fewer, `/setup` does not mark the profile complete. Say so
  explicitly rather than proceeding quietly.
- When the CV, the profile and the reference folder name **different** referees, show
  the three lists side by side and ask which is current. Do not merge them.
- Letters come from referees directly. Never draft, simulate or offer to draft one,
  and do not track whether a letter has been sent - that is between the user and
  their referees.

Write the table into `01-candidate-profile.md`.

---

## Step 4: Statements

Read every file in `documents/statements/`. Expect a research statement and a
teaching statement; match by filename, and ask if the mapping is ambiguous.

**Assess the research statement** against what a committee looks for:

- **Agenda** - is the statement organised around a question, or is it a list of papers?
- **Job market paper** - is one identified, with its status and file? If the statement
  names a different paper than `01-candidate-profile.md`, ask; do not choose.
- **Pipeline** - under review, working papers, in preparation, each with a target.
- **Funding record** - grants held, role, amounts. None is a fact to frame, not a hole.
- **Three-to-five year plan** - does it commit to anything specific?

**Assess the teaching statement**:

- **Philosophy** - what claim does it make, and does the record support it?
- **Courses taught** - instructor of record, TA and guest lecture kept distinct.
- **Evaluations** - scores on file, or "none on file". Never estimate one.
- **Courses you can teach** - ready now, and with one term of preparation. Ask for
  this list if the statement does not contain it; every cover letter's teaching
  paragraph is built from it.

Write the assessment, the gaps and the source paths into `08-statements.md`. **Do not
copy the statement text into the profile** - the file in `documents/statements/` is
the single source, and `/apply` reads it directly.

If a statement is missing, say which, point at `templates/statement.tex`, and record
it as a gap. Never draft a research or teaching statement from scratch here: it is
the user's own argument about their own work.

Diversity, service and mentoring statements are **not** collected here. `/apply`
handles them per posting.

---

## Step 5: Search configuration

Write `.claude/skills/job-scraper/search-queries.md`.

Ask three things:

1. **Appointment types.** Which of tenure-track, tenured, visiting,
   teaching-track/lecturer, postdoctoral, research professor are in scope? Anything
   not ticked is excluded by `/scrape`'s appointment gate, so ask directly rather
   than assuming. Pre-doctoral and research-assistant posts are never in scope.
2. **Field terms.** The primary field, three to five subfields, and the methods that
   actually appear in postings. Short terms: boards index terse keywords.
3. **Countries.** Where the user will take a position. Relocation is assumed; there
   is no commute radius in an academic search.

Then add the `site:` queries for the boards without a fetcher, substituting the
field terms, and any department the user names directly.

---

## Step 6: Fill the remaining gaps

Ask only for what the documents could not supply:

- Languages and levels, if not on the CV (feeds the Language Gate)
- What kind of department they want, and what they want to avoid (feeds career
  alignment scoring and `02-behavioral-profile.md`)
- Paper size for the packet: US letter or A4. Write it into `templates/preamble.tex`.
- The name to use in `templates/preamble.tex` and `templates/cover_letter.tex`

---

## Step 7: Write

Write these files, replacing every `[BRACKETED]` token you have an answer for and
leaving the rest visible:

- `01-candidate-profile.md` - the full record, including the referee table
- `02-behavioral-profile.md` - from the answers in Step 6 and the language of any
  reference letters read, each inferred line labelled *[inferred - review]*
- `04-job-evaluation.md` - the strong/moderate/weak field lists
- `07-interview-prep.md` - STAR **stubs** from real achievements. Never invent the
  situation, action or result; leave those lines empty for the user
- `08-statements.md` - assessment, gaps, source paths
- `.claude/skills/job-scraper/search-queries.md` - the search configuration
- `templates/preamble.tex` and `templates/cover_letter.tex` - name and paper size

Set **Profile status** in `01-candidate-profile.md` to `complete` only when there are
at least three referees **and** both statements are on file and assessed. Otherwise
leave it `incomplete` and list what is missing.

Make targeted edits. Do not rewrite a file whose content is already correct, and
never overwrite a section the user has edited without showing the conflict first.

---

## Step 8: Report

```
## Setup complete - profile status: [complete | incomplete]

Written: [files]
Referees on file: [N]  (minimum 3)
Statements: research [assessed | missing], teaching [assessed | missing]
Gaps to close: [list]

Next: /scrape to find postings, then /rank.
```

Re-run any time with `--section <name>`; the command is safe to re-run as documents
are added.
