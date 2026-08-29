# Setup

From nothing to a first application packet. Fifteen minutes, most of it installing
LaTeX.

---

## 1. Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Or use the desktop app, the web app at claude.ai/code, or an IDE extension. Any of
them can open this folder.

## 2. LaTeX

The packet compiles with `pdflatex`. Nothing else is needed - no fontspec, no
xelatex, no font files.

| System | Install |
|---|---|
| macOS | [MacTeX](https://tug.org/mactex/) (large), or BasicTeX plus `sudo tlmgr install titlesec enumitem lastpage needspace` |
| Linux | `sudo apt install texlive-latex-recommended texlive-latex-extra` |
| Windows | [MiKTeX](https://miktex.org/) - it installs missing packages on first compile |

Check it:

```bash
pdflatex --version
```

## 3. Python

Python 3.10 or newer. `tools/boards.py` uses the standard library only - no `pip
install`, no virtual environment.

```bash
python3 --version
```

`tools/lint_skills.py` is the one exception: it wants PyYAML, and only contributors
need it (`pip install pyyaml`, or run it with `uv run --with pyyaml python3
tools/lint_skills.py`).

## 4. Get your own copy

On <https://github.com/noejn2/ai-academic-job-search> click **Use this template**,
name your copy and make it **private** - it will hold your publication record,
referees and contact details once `/setup` runs. Then:

```bash
git clone git@github.com:<you>/<your-copy>.git
cd <your-copy>
```

Not the Fork button: a fork of a public repository can never be made private, and
`/setup` will warn you about exactly that.

## 5. Add your documents

The workspace reads `documents/`. See `documents/README.md` for the full layout.

**Required:**

- `documents/cv/<your_cv>.tex` - your master academic CV, as LaTeX source. This
  workspace ships no CV template: `/apply` tailors a copy of *your* CV per posting,
  so a PDF is not enough.

**Strongly recommended:**

- `documents/statements/research_statement.tex` and `teaching_statement.tex` - your
  own statements. `/setup` assesses them and reports gaps; `/apply` tailors copies
  per posting. If you have not written them yet, `templates/statement.tex` is a
  skeleton, but the argument has to be yours.
- `documents/references/` - your referee list (`.txt`, `.md`, `.pdf`, or `.rtf`),
  with name, title, institution, email and relationship. At least three.

**Useful:**

- `documents/papers/` - job market paper, writing samples
- `documents/teaching/` - syllabi, evaluation reports
- `documents/diplomas/` - transcripts, in case a posting asks for all of them

## 6. Keep it private

Your `documents/`, packets, tracker and scrape state are gitignored. The profile
files under `.claude/skills/job-application-assistant/` are **tracked**, and after
`/setup` they hold your record - publications, referees, contact details.

If you made your copy private in step 4, you are done. If you cloned this
repository directly instead, either keep those commits local and never push, or
move them to a private repository of your own:

```bash
gh repo create my-academic-search --private --source=. --remote=origin --push
```

`/setup` checks your `origin` before it writes anything and warns you if it is
public. `python3 tools/security_guards.py` fails if the personal-data ignore rules
are ever weakened.

## 7. First run

In Claude Code, in this folder:

```
/setup
```

It reads `documents/`, asks about anything missing, collects your referees (three
minimum), assesses your statements, and writes your search configuration. Then:

```
/scrape          # sweep the boards
/rank            # score what came back
/apply <url>     # build a packet
```

## 8. Later

- `/setup --section referees` or `--section statements` or `--section search` to
  update one part
- `/outcome <institution>` after you submit, and again at every stage
- `/interview <institution>` once an interview or flyout is scheduled
- `/reset` to clear everything back to placeholders

## Troubleshooting

**`/setup` stops saying it needs a `.tex` CV.** It does. Export your CV to LaTeX
source, or write one - the workspace tailors your own file rather than re-keying your
record into a template.

**`pdflatex` fails on a missing package.** BasicTeX and minimal TeX Live ship without
`titlesec`, `enumitem`, `lastpage` or `needspace`. Install them with `tlmgr install
<name>`; MiKTeX does it automatically.

**A board returns nothing.** Run `python3 tools/boards.py --board joe --format table`
directly to see the error. Boards change their markup; the parsers live in
`tools/boards.py` and the tests in `tests/test_boards.py` show what shape each parser
expects.

**Page references show as `??`.** The document was compiled once. Every `.tex` in a
packet needs `pdflatex` run twice.
