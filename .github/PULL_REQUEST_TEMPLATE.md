## What this changes

<!-- One or two sentences. -->

## Checks

```bash
python3 -m unittest discover -s tests -t .
python3 tools/security_guards.py
python3 tools/lint_skills.py          # needs PyYAML
```

- [ ] Tests pass
- [ ] Guards pass
- [ ] Lint passes

## Ground rules

- [ ] No personal data. Tracked profile files still carry their `[BRACKETED]` placeholders and `<!-- SETUP: -->` markers
- [ ] No new dependencies. Python standard library and `pdflatex` only
- [ ] Academic scope only. Nothing here is for industry, government, think-tank or national-lab applications
- [ ] Nothing drafts, templates or attaches a reference letter
- [ ] If a command's prose changed a contract string (tracker header, status vocabulary, compile instruction), the test asserting it changed in the same commit
- [ ] If a board parser changed, `tests/fixtures/` has a trimmed fixture proving the new shape
