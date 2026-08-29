# templates/

The LaTeX skeletons `/apply` copies into an application packet. All three are
plain `article`-class documents compiled with **pdflatex, run twice**.

| File | Used for |
|---|---|
| `preamble.tex` | Shared by every document in a packet. `\input{preamble}` at the top of each file. Holds the paper size, margins, fonts, link colours and the `\hdr` title macro. |
| `statement.tex` | Research, teaching, diversity, service, mentoring - any statement a posting asks for. |
| `cover_letter.tex` | The packet's cover letter. |

There is **no CV template here.** Your CV is your own file: `/setup` reads the
`.tex` you keep in `documents/cv/`, and `/apply` tailors a copy of it per
posting. See `.claude/skills/job-application-assistant/05-cv-tailoring.md`.

`[BRACKETED]` tokens are placeholders. `/setup` fills the ones it knows (your
name, paper size); `/apply` fills the rest per posting.
