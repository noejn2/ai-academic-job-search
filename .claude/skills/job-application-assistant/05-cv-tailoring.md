# Academic CV

## Your CV is your own file

This workspace ships **no CV template**. An academic CV is a document you already
maintain, in a layout your field expects, and re-keying it through a template loses
formatting a committee reads as care.

- **Master:** the `.tex` file you keep in `documents/cv/`. `/setup` requires one and
  stops without it.
- **Per posting:** `/apply` copies it to `applications/<institution>_<role>/cv.tex`
  and tailors the copy. The master is never edited by a command.
- **Compile:** `pdflatex -interaction=nonstopmode cv.tex`, **run twice**. A CV with a
  `lastpage` footer or any `\ref` needs the second pass or the footer is wrong.
  If your CV needs a different engine, say so in a comment at the top of the file and
  `/apply` will use it.

If your master CV lives only as a PDF, `/setup` says so and asks for the source. A
PDF cannot be tailored.

## What tailoring means here

Reordering and emphasis. **Never cutting.**

- **Move the sections the posting cares about earlier.** A markets-and-risk search
  wants publications and research interests high; a teaching-weighted posting wants
  teaching and mentoring above working papers.
- **Rewrite the research-interests paragraph** to speak to the department's stated
  emphases, using only work that already exists in the CV.
- **Never cut a publication, grant, award or course to save space.** There is no page
  limit on an academic CV; length is the record, not a defect. The two-page
  discipline of an industry résumé is exactly wrong here.
- **Never add a line the master CV does not contain.** New facts go into
  `01-candidate-profile.md` first, then into your master CV, then into a tailored
  copy - in that order.
- **No ATS check.** A search committee reads the PDF. No parser sits in front of it,
  so keyword extraction from the text layer is not run, and its absence is stated in
  the report rather than silently skipped.

## Verification

- [ ] Compiles clean with `pdflatex` run twice
- [ ] Page count is whatever the record needs
- [ ] No section heading orphaned at the foot of a page with its content overleaf
- [ ] The research-interests paragraph names the department's actual emphases
- [ ] Every factual claim still matches `01-candidate-profile.md`
- [ ] Contact details are current

Fixes for the two layout problems that actually occur:

- **Orphaned heading:** `\usepackage{needspace}` in the preamble, then
  `\needspace{5\baselineskip}` before the section.
- **A section spilling by two lines:** `\enlargethispage{2\baselineskip}`. Never
  shrink the geometry or the font.

## LaTeX special characters

Escape `\&`, `\%`, `\$`, `\#`, `\_` in any text inserted into a `.tex` file - an
institution name with an ampersand ("Texas A&M") breaks the compile silently at the
worst moment. `~` and `^` need `\textasciitilde{}` and `\textasciicircum{}`.
Never write `\item[` with an unbraced bracket argument.
