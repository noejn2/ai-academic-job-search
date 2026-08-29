# /interview - Prepare for an Interview or Flyout

You are preparing the user for a scheduled stage of a real search. The frameworks
already exist - `07-interview-prep.md` and the department research checklist in
`04-job-evaluation.md` - and the packet holds what was actually submitted. This
command wires them into a stage-specific pack.

`$ARGUMENTS` is an institution name, optionally followed by a stage
(`interview` or `flyout`). With no stage, read it from the tracker.

---

## Step 1: Load the application

Match the argument against `job_search_tracker.csv` and `applications/*/`. Read from
the packet: `job_posting.md`, `cover_letter.tex`, `research_statement.tex`,
`teaching_statement.tex`, `cv.tex`, `checklist.md` and `outcome.md` if present.

**Everything prepared here must match what was submitted.** The committee has read
those documents; an answer that contradicts them costs more than a weak answer.

If the tracker status is `drafted` or `applied` and the user is asking for a pack
anyway, say the stage is not recorded, ask which it is, and continue.

---

## Step 2: Research the department

Follow the department research checklist in `04-job-evaluation.md`, from the
department's own pages: who is on the committee if it is public, what the field
faculty work on, what the last two hires were, the seminar series, the courses named
in the posting, and the graduate programme. Verify each claim against a page you
fetched.

---

## Step 3: Build the pack

Write `applications/<institution>_<role>/prep_<stage>.md`.

### Both stages

- **Their questions, your answers.** Take the standard list in `07-interview-prep.md`
  and answer each *for this department*, in the user's own record. Flag any answer
  that is thin.
- **The three questions this posting invites** - drawn from the gaps named in the
  fit evaluation and the statements. Prepare those first; they are the ones that
  will be asked.
- **Your questions for them**, specific to what the research turned up.
- **Consistency check** - anything in the packet a committee member would push on.

### Interview (first round)

- Two-minute and five-minute versions of the job market paper.
- One sentence on the contribution for a non-specialist.
- The teaching answer built from the courses this posting names.
- Logistics: format, length, who is in the room, time zone.

### Flyout

- **Job talk plan**: which paper, the arc, where interruptions land, the three
  hostile questions answered inside the talk, and what breaks if the identification
  assumption fails.
- **Teaching demonstration**: the topic asked for, a real lesson at the level asked,
  one moment where students do something, and a syllabus for the course named.
- **One-on-ones**: a line per faculty member on what to ask them, from their work.
- **Chair and dean**: startup, teaching load, tenure clock, what the department needs
  from this line.
- **Stamina**: the schedule, meals as interviews, and what to say to graduate students.

---

## Step 4: Offer a mock

Ask whether to run a mock interview or a mock job-talk Q&A. If yes, stay in role, one
question at a time, follow up once on a weak answer, and give feedback only at the
end: what landed, what was vague, what a committee would push on.

---

## Step 5: Rules

- Write only to `applications/<institution>_<role>/prep_<stage>.md`, except that a
  STAR example the user confirms is appended to `07-interview-prep.md`, and a new
  fact is written to `01-candidate-profile.md`.
- Never invent a committee member, a course, or a departmental fact.
- Never contradict what the packet says.
