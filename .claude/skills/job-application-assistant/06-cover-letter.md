# Cover Letter

An academic cover letter is a plain typed letter, not a designed document. It
shares `templates/preamble.tex` with the packet's statements so the whole
application reads as one document, and compiles with **pdflatex, run twice**.

Output: `applications/<institution>_<role>/cover_letter.tex` and `.pdf`.

## Length

**One page by default.** A committee reading two hundred letters does not reward
length.

**Two pages when the posting requires the letter itself to carry more** - for
example "a letter of application that includes a statement of professional goals for
teaching and research". When the letter must do the work of a research statement and
a teaching statement, two pages is correct, and compressing to one loses required
content. Say in the report that the second page is a requirement, so the page count
reads as a decision rather than an overrun.

If it spills by a little, compress the letterhead to a name line plus one
pipe-separated contact line before cutting content. Never shrink the geometry.

## Structure

1. **Open on the position, not on enthusiasm.** Name the post in the search's own
   words and give its vacancy or requisition number - academic postings have one and
   portals index on it.
2. **Research paragraph.** The agenda, the job market paper or flagship result, and
   what it means for this department. Concrete: a paper, a journal, a number.
3. **Teaching paragraph.** The courses the posting names that you can teach, and the
   evidence. Where the record is thin, say so here rather than letting the committee
   find it in the CV.
4. **Fit paragraph.** The department's stated emphases, colleagues, centres or data
   you would work with, drawn from research you verified. Never flattery, never
   "your prestigious institution".
5. **Close with the enclosures**, matching the posting's required-document list
   exactly, and one line on how references will reach them.

## Rules

- **Address the named search chair** when the posting gives one; otherwise "Dear
  Members of the Search Committee".
- **State gaps plainly.** Committees verify against the CV, and an unclaimed gap
  found later costs more than one volunteered early.
- **Every claim traceable** to `01-candidate-profile.md`, the master CV, or a
  statement in `documents/statements/`.
- **Match the posting's language** (an appointment advertised in Spanish gets a
  Spanish letter). The CV language is a profile-level setting and does not change per
  posting.
- **No em-dashes, no cliches, no apologetic hedging** - see `03-writing-style.md`.
- Escape LaTeX special characters: `\&`, `\%`, `\$`, `\#`, `\_`.

## Verification

- [ ] Compiles clean with `pdflatex` run twice
- [ ] One page, or two with the posting's requirement named in the report
- [ ] Signature block on the same page as the body
- [ ] Position named as the posting names it, with its vacancy number
- [ ] Addressed to the search chair when the posting names one
- [ ] Enclosure list matches the posting's required documents exactly
