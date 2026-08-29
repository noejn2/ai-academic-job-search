# Contributing

Bug reports and pull requests are welcome, particularly board parsers that break when
a board changes its markup - that will happen, and it is the most useful fix.

## Before you open a pull request

```bash
python3 -m unittest discover -s tests -t .
python3 tools/security_guards.py
uv run --with pyyaml python3 tools/lint_skills.py     # or pip install pyyaml
```

CI runs the same three plus a LaTeX smoke test on the shipped templates.

## Ground rules

**No personal data.** Every tracked file ships with `[BRACKETED]` placeholders and a
`<!-- SETUP: -->` marker. `tests/test_placeholders.py` fails if a profile
file loses them, which is what stops someone's referees from being committed by
accident.

**No new dependencies.** Python standard library only, and `pdflatex` for LaTeX. A
contributor should not have to install anything to run the pipeline. PyYAML is the
single exception and is needed only by the skill linter.

**Academic scope only.** This workspace applies to positions hired by a university or
college department. A feature that only makes sense for industry, government, think
tanks or national labs belongs in the upstream template
(<https://github.com/MadsLorentzen/ai-job-search>), not here.

**Never a reference letter.** No feature may draft, simulate, template or attach one.

**Commands are prose, and prose is tested.** A command file is a specification an
agent follows literally. Several tests assert exact strings in these files - a
tracker header, a status vocabulary, a compile instruction - because those strings
are the contract between two commands. Change the string and the test in the same
commit; do not delete the test.

## Adding a board parser

`tools/boards.py` holds one `parse_<board>` function per board, each taking `bytes`
and returning records in the shared shape. To add one:

1. Check the board's published policy first: `python3 tools/robots_check.py
   '<listings URL>'`. A non-zero exit means the site has declined; add a `site:`
   query to `search-queries.md` and stop - do not probe it with browser headers.
   The gate is the same one `09-web-research.md` puts in front of the retry, and it
   applies to a contributor exploring a board exactly as it applies at runtime.
2. Only then confirm the board serves listings to a plain client, using the
   browser-header `curl` in `09-web-research.md`. If it needs JavaScript, add a
   `site:` query instead - that is not a defeat, it is the cheaper answer.
3. Write the parser, register it in `PARSERS` and `URLS`, add it to `BOARDS`.
   `boards.py` calls it through `parse()`, so a parser that raises on changed
   markup degrades that one board instead of aborting the sweep.
4. Save a **trimmed** fixture with two listings in `tests/fixtures/`, and add a test
   asserting the fields it must extract. Never commit a full board dump.

## Style

Match the surrounding files. Command prose is direct and second person, explains why
a rule exists where the reason is not obvious, and avoids em-dashes.
