<!-- SETUP: /setup calibrates the match areas and career section from your profile. Replace every [BRACKETED] token. -->

# Job Evaluation Framework

How a posting is scored, by `/rank` in batch and by `/apply` Step 1 in depth. The
two use the same rubric; `/apply` adds department research and is authoritative.

---

## Gates - run before scoring

A posting failing any gate is not scored. Report which gate fired; never soften a
gate into a low score.

### 1. Appointment gate
The appointment types in `.claude/skills/job-scraper/search-queries.md` are the ones
in scope. A posting outside them is out, however good the fit.

Always out, whatever is configured: pre-doctoral and research-assistant posts, and
any position not hired by a university or college department. Industry, government
agencies, national labs, think tanks and NGOs are out of scope even when the
research is identical - a research post *inside* a university stays in.

### 2. Eligibility gate
Degree requirement (in hand vs. expected by the start date), work authorization for
the posting's country, and any stated requirement the profile cannot meet.

### 3. Country gate
Countries listed in `search-queries.md`. Relocation is assumed within them.

### 4. Language gate
A required working language absent from the Languages table in
`01-candidate-profile.md` is a hard fail. A higher level in a listed language is a
flag for the user's judgment, not an automatic fail.

---

## Scoring dimensions

Three dimensions, weighted. Score each 0-100 with the evidence beside it.

### 1. Research fit - 50%
- Does the posting's stated field match the agenda in `08-statements.md`?
- Do the methods it names appear in the record, or only adjacent to it?
- Are the venues it expects the venues in `01-candidate-profile.md`?
- Does the department's own work connect to the job market paper?
- Is there a centre, dataset, lab or collaborator named that the record speaks to?

**Strong match areas:** [YOUR_STRONGEST_FIELDS]
**Moderate:** [ADJACENT_FIELDS]
**Weak:** [FIELDS_YOU_DO_NOT_CLAIM]

### 2. Teaching fit - 30%
- Which named courses can you teach now, which with a term of preparation, which not
  at all? (`08-statements.md`, "Courses you can teach")
- Load versus record: a 3-3 with no instructor-of-record experience is a real risk
  and is scored as one, not hidden.
- Level: undergraduate service teaching, master's methods and PhD field courses ask
  for different evidence.
- Does the posting want a teaching statement, evaluations or a demo you cannot
  supply? Note it - it lands in the packet checklist.

### 3. Career alignment - 20%
- Department type and where it sits: R1, R2, liberal arts, business school, policy
  school, agricultural experiment station.
- What the posting asks you to become: a grant-funded PI, a teaching backbone, an
  extension appointment. Compare with the user's stated direction and drains in
  `02-behavioral-profile.md`.
- Start date, tenure clock, and whether the appointment is 9-month or 12-month.
- Location, family and dual-career considerations the user recorded.

---

## Weighting and thresholds

```
score = 0.50*research + 0.30*teaching + 0.20*career
```

| Band | Score | Meaning |
|---|---|---|
| Strong fit | 75-100 | Apply. |
| Good fit | 60-74 | Apply unless the calendar is full. |
| Moderate fit | 45-59 | Apply if the department or location is a draw. |
| Weak fit | 30-44 | Only with a specific reason. |
| Poor fit | 0-29 | Skip. |

No salary dimension: academic salaries are set by rank and institution, not
negotiated per posting at application time.

---

## Output format

```markdown
## Fit: [Role] - [Department], [Institution]

| Dimension | Weight | Score | Evidence |
|---|---|---|---|
| Research fit | 50% | [N] | [what matched, what did not] |
| Teaching fit | 30% | [N] | [courses named vs. courses you can teach] |
| Career alignment | 20% | [N] | [department type, appointment, start date] |
| **Overall** | | **[N]** | **[band]** |

**Gates:** appointment [pass/fail], eligibility, country, language.

### Strengths for this search
### Gaps, stated plainly
### Required documents (from the posting, verbatim)
### Recommendation
```

---

## Department research checklist

Run by `/apply` Step 3, not by `/rank`. Search from the department's own site, never
from a link inside the posting.

- Faculty in the posting's field: who would you be joining, and what do they work on?
- Recent hires: what did the department actually hire in the last three years?
- Seminar series, centres, labs, datasets, experiment stations.
- Graduate programme: fields offered, students you would supervise.
- Teaching: the actual catalogue entries for the courses the posting names.
- Anything in the department's news the letter can honestly connect to.

Verify every claim against a page you fetched. A search snippet is a lead, not a
source.

---

## Calibration from past applications

`/setup` Step 2 appends here after reading `applications/*/outcome.md`. Do not edit
by hand. `/reset` clears it: it is derived from your own search history.
