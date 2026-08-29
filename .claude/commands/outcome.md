# /outcome - Record What Happened

You are recording the state of an application: submitted, invited to interview,
invited to a flyout, offered, or closed. The data lands in two places nothing else
writes:

- `job_search_tracker.csv` - the status column `/rank` and `/apply` read for dedup
- `applications/<institution>_<role>/outcome.md` - the per-application record
  `/setup` mines to calibrate `04-job-evaluation.md`

`$ARGUMENTS` is an institution name, a packet folder, or empty (then list open
applications and ask which).

---

## Tracker status vocabulary

The academic search runs in four steps, and the tracker mirrors them.

| Status | Means |
|---|---|
| `drafted` | `/apply` built the packet; not submitted |
| `applied` | Submitted to the department or portal |
| `interview` | Invited to a first-round interview (video, or at a conference) |
| `flyout` | Invited to the campus visit: job talk, teaching demo, one-on-ones |
| `offer` | An offer is on the table |
| `hired` | Offer accepted |
| `offer_declined` | Offer received and declined |
| `rejected` | Turned down at any stage |
| `no_response` | Deadline long past, no contact, search apparently closed |
| `withdrawn` | The user withdrew |

**Final:** `hired`, `rejected`, `no_response`, `offer_declined`, `withdrawn`.
**Open:** everything else. Statuses use underscores, never spaces. These are the same
values everywhere in the workspace, not separate vocabularies per command; a row with
a final status is never reopened or overwritten - a fresh application to the same
department in a later cycle gets its own row.

Status only moves forward. `interview` never becomes `applied` again.

---

## Step 1: Load and identify

Read `job_search_tracker.csv` and glob `applications/*/`. Match the argument
case-insensitively against institution, then against role. On several matches, list
them and ask. On none, say so and offer to add a row for an application made outside
this workspace.

---

## Step 2: Ask what happened

One question, then follow up:

> "Where does [Institution] stand? Submitted, first-round interview, flyout, offer,
> or closed?"

For an **interview** or **flyout**, also collect: date, format (video, conference,
campus), who was in the room, and what they asked. This is what `/interview` builds
the next pack from, and what makes the record worth keeping.

For a **rejection**, ask at which stage and whether any feedback was given. Feedback
is rare and valuable; record it verbatim.

---

## Step 3: Write

### `outcome.md` in the packet

```markdown
# Outcome: [Institution] - [Role]

**Status:** [status]
**Deadline:** [YYYY-MM-DD]   **Submitted:** [YYYY-MM-DD]
**Resolved:** [YYYY-MM-DD or blank]

## Stages
- [ ] Application submitted
- [ ] First-round interview
- [ ] Flyout (campus visit)
- [ ] Job talk
- [ ] Teaching demonstration
- [ ] Offer

## Contacts
[Search chair, who interviewed, who to thank.]

## What they asked
[Questions, verbatim where remembered. Feeds /interview and 07-interview-prep.md.]

## Notes
[What happened. What you would do differently. Any signal about what they valued.]
```

Keep earlier content; append rather than overwrite. Never invent a date.

### Freeze what was submitted

**When the status moves to `applied`, snapshot the packet.** Copy every document the
user sent - the `.tex` sources, their PDFs, `references.md`, `checklist.md` and
`job_posting.md` - into `applications/<institution>_<role>/submitted/`, and write
`submitted/SUBMITTED.md` naming the submission date and listing what went.

This is the moment "what was submitted" becomes a fact. Before it, the packet is a
draft that `/apply` may rewrite; after it, the committee has read a specific set of
documents and `/interview` must prepare against those, not against a later re-draft.

- **Never overwrite an existing `submitted/`.** If the user genuinely resubmitted,
  ask, then write `submitted_<YYYY-MM-DD>/` beside it and say which is current.
- Ask the user to confirm the packet on disk is what they actually sent. If they
  edited anything outside this workspace, or the portal took a different file, record
  that in `SUBMITTED.md` rather than freezing a copy that is quietly wrong.
- If the folder holds no compiled PDFs, say so; freeze the sources and note that the
  PDFs the committee read were not kept.

### Tracker row

Update `status`, `notes` (append a dated line), `contact_person` when the stage named
one, and - **only on the move off `drafted`** - `date`, which becomes the actual
submission date. `/apply` wrote the draft date into that column, so leaving it makes
every follow-up calculation and the "awaiting response past 30 days" count in Step 5
run off a date the application was not sent on. Nothing else changes. Never
restructure the CSV, reorder rows, or touch another row.

---

## Step 4: Follow-up branch

`/outcome followup <N>` drafts a follow-up message for the application in row N.

- **Draft only, never send.** Print it for the user to copy.
- No new claims: everything in it comes from the packet and the profile.
- **Maximum two follow-ups per application.**
- Nothing before **30 days** of silence past the deadline, or past the date the
  department said it would decide. Academic searches are slow, and a committee that
  has not met yet cannot answer.
- After an interview or flyout, a thank-you within 48 hours is a different thing and
  is always appropriate.

---

## Step 5: Report

```
## [Institution] - [Role]: [old status] -> [new status]

Written: applications/<...>/outcome.md, tracker row [N]
Open applications: [N]  ([M] awaiting response past 30 days)
```

If the new status is `interview` or `flyout`, end with: "Run `/interview
<institution>` to build the prep pack."
