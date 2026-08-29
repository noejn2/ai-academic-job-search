# /reset - Clear Personal Data

You are returning this workspace to the state it ships in: profile files back to
their placeholders, personal documents and packets removed. Someone runs this to hand
the repository on, to start a second search from scratch, or to check that the
template still ships clean.

**This deletes work that cannot be recovered.** Nothing is deleted before Step 2.

---

## Step 1: Show what would go

Glob and count, then print exactly what will be removed and what will be reset:

```
## Files that would be deleted

documents/cv/          [N files]
documents/statements/  [N files]
documents/papers/      [N files]
documents/references/  [N files]
documents/teaching/    [N files]
documents/diplomas/    [N files]
documents/postings/    [N files]
applications/          [N packets]
job_scraper/seen_jobs.json  [N postings seen]
job_search_tracker.csv      [N rows]

## Files that would be reset to placeholders

.claude/skills/job-application-assistant/01-candidate-profile.md
.claude/skills/job-application-assistant/02-behavioral-profile.md
.claude/skills/job-application-assistant/04-job-evaluation.md
.claude/skills/job-application-assistant/07-interview-prep.md
.claude/skills/job-application-assistant/08-statements.md
.claude/skills/job-scraper/search-queries.md
templates/preamble.tex
templates/cover_letter.tex

## Not touched

03-writing-style.md, 05-cv-tailoring.md, 06-cover-letter.md, SKILL.md files,
commands, tools, tests, documentation - none of these hold personal data.
```

## Step 2: Confirm

> This deletes every document, packet, tracker row and scrape record listed above, and
> resets the profile files to the placeholders the template ships with. It cannot be
> undone. Type the number of packets that will be deleted to confirm.

Accept only the correct number. Anything else stops the command.

## Step 3: Delete

```bash
rm -rf documents/cv/* documents/statements/* documents/papers/* documents/references/* \
       documents/teaching/* documents/diplomas/* documents/postings/*
rm -rf applications/*/
rm -f job_scraper/seen_jobs.json
```

Keep every `.gitkeep`. Reset `job_search_tracker.csv` to its header line alone:

```
date,institution,department,role,appointment,status,fit_rating,contact_person,notes,packet,source,deadline
```

## Step 4: Reset the profile files

For each file in the reset list, restore the shipped version: every `[BRACKETED]`
placeholder back in place, the `<!-- SETUP: ... -->` comment on the first line, no
personal data anywhere. Restore `Profile status: incomplete` in
`01-candidate-profile.md`.

If the repository is a git checkout and the file is tracked and unmodified upstream,
`git checkout -- <file>` is the reliable way. Otherwise rewrite the file from its
placeholder structure.

## Step 5: Verify and report

Grep the reset files for anything that looks personal - an `@` in an email position,
a four-digit year in a publication line, a name in the `\hdr` macro. Report:

```
## Reset complete

Deleted: [counts]
Reset: [files]
Remaining personal data found: [none | list]

Run /setup to build a profile again.
```

If anything is still there, say so loudly. A template that ships someone's referees
is the failure this command exists to prevent.
