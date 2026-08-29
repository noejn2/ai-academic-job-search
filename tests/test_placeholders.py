"""What ships must be a template, not someone's job search.

The profile files are tracked, unlike documents/ and applications/. After
/setup they hold a real person's record - publications, referees, contact
details. These tests are what stops that state from being committed and
published: every tracked file a command writes into must still carry its
placeholders when the repository is packaged.
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import REPO_ROOT, git_ignores, shipped_files  # noqa: E402
PROFILE = REPO_ROOT / ".claude" / "skills" / "job-application-assistant"

# Files /setup or /apply write personal data into. Each ships with a SETUP
# marker and at least one [BRACKETED] token.
FILLED_BY_SETUP = [
    PROFILE / "01-candidate-profile.md",
    PROFILE / "02-behavioral-profile.md",
    PROFILE / "03-writing-style.md",
    PROFILE / "04-job-evaluation.md",
    PROFILE / "07-interview-prep.md",
    PROFILE / "08-statements.md",
    REPO_ROOT / ".claude" / "skills" / "job-scraper" / "search-queries.md",
]

TEMPLATES = [
    REPO_ROOT / "templates" / "preamble.tex",
    REPO_ROOT / "templates" / "statement.tex",
    REPO_ROOT / "templates" / "cover_letter.tex",
]

def read_section(path, heading):
    """The body under an exact heading line, up to the next heading."""
    lines = path.read_text(encoding="utf-8").splitlines()
    body = []
    for line in lines[lines.index(heading.rstrip()) + 1:]:
        if re.match(r"#{1,4} ", line):
            break
        body.append(line)
    return "\n".join(body)


PLACEHOLDER = re.compile(r"\[[A-Z][A-Z_0-9 ]*\]")
# The SETUP marker itself says "replace every [BRACKETED] token", and that
# sentence matches PLACEHOLDER. A file whose real placeholders had all been
# filled in therefore passed on the strength of the marker's own prose.
PROSE_TOKENS = {"[BRACKETED]"}


def real_placeholders(text):
    """Placeholders in the body, not the word "[BRACKETED]" in the marker."""
    body = "\n".join(
        line for line in text.splitlines() if not line.startswith(SETUP_MARKER)
    )
    return [token for token in PLACEHOLDER.findall(body) if token not in PROSE_TOKENS]
SETUP_MARKER = "<!-- SETUP:"

# Everything tracked. documents/ and applications/ are gitignored, so a file
# there is the user's own and none of this applies to it.
TRACKED_TEXT = shipped_files(
    "*.md", ".claude/**/*.md", ".claude/**/*.json", "templates/*.tex",
    "tools/*.py", "tests/*.py", "*.csv", ".github/**/*",
)


class GuardCoverageTests(unittest.TestCase):
    """FILLED_BY_SETUP must be derived from /setup, not remembered by hand.

    03-writing-style.md was written by /setup Step 7 and absent from this list
    for two releases, so a fork could run /setup, have its own letter patterns
    appended, push, and every test here would pass.
    """

    def test_every_markdown_file_setup_writes_is_guarded_here(self):
        step7 = read_section(REPO_ROOT / ".claude" / "commands" / "setup.md", "## Step 7: Write")
        written = re.findall(r"^- `([\w./-]+\.md)`", step7, re.M)
        self.assertGreaterEqual(len(written), 6, "Step 7's file list did not parse")
        guarded = {path.name for path in FILLED_BY_SETUP}
        for target in sorted(written):
            with self.subTest(target=target):
                self.assertIn(
                    Path(target).name, guarded,
                    f"/setup Step 7 writes {target} but FILLED_BY_SETUP does not guard it",
                )

    def test_every_tex_file_setup_writes_is_guarded_as_a_template(self):
        step7 = read_section(REPO_ROOT / ".claude" / "commands" / "setup.md", "## Step 7: Write")
        written = re.findall(r"`([\w./-]+\.tex)`", step7)
        self.assertTrue(written, "Step 7 names no .tex file")
        guarded = {path.name for path in TEMPLATES}
        for target in sorted(set(written)):
            with self.subTest(target=target):
                self.assertIn(Path(target).name, guarded)


class PlaceholderTests(unittest.TestCase):
    def test_every_setup_written_file_ships_a_marker_and_placeholders(self):
        for path in FILLED_BY_SETUP:
            with self.subTest(file=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertTrue(
                    text.startswith(SETUP_MARKER),
                    f"{path.name} must open with a {SETUP_MARKER} comment",
                )
                self.assertTrue(
                    real_placeholders(text),
                    f"{path.name} has no [BRACKETED] placeholder left - "
                    "it looks filled in, which means personal data may ship",
                )

    def test_the_templates_ship_placeholders(self):
        for path in TEMPLATES:
            with self.subTest(file=path.name):
                self.assertTrue(
                    PLACEHOLDER.search(path.read_text(encoding="utf-8")),
                    f"{path.name} has no placeholder left",
                )

    def test_the_profile_ships_incomplete(self):
        text = (PROFILE / "01-candidate-profile.md").read_text(encoding="utf-8")
        self.assertIn("**Profile status:** incomplete", text)


class NoPersonalDataTests(unittest.TestCase):
    """Cheap signatures of a filled-in profile, checked across every tracked file."""

    def test_no_real_email_address(self):
        # A placeholder email is [YOUR_EMAIL] or your.email@example.com; anything
        # else with an @ and a dotted domain is somebody's actual address.
        pattern = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
        allowed = re.compile(r"(example\.(com|org)|your\.email|\[|@[\w-]*\.?(edu|com)\b(?=\W*\]))")
        for path in TRACKED_TEXT:
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in pattern.finditer(text):
                address = match.group(0)
                if allowed.search(address) or "example" in address:
                    continue
                if address.startswith("git@github.com"):
                    continue  # an SSH clone URL, not a mailbox
                # Institutional addresses in prose examples are the only other
                # legitimate case, and there are none: fail loudly.
                self.fail(f"{path.relative_to(REPO_ROOT)}: real-looking email {address!r}")

    def test_no_phone_number(self):
        pattern = re.compile(r"\+\d{1,3}[\s(]\(?\d{2,4}\)?[\s-]\d{3}[\s-]\d{3,4}")
        for path in TRACKED_TEXT:
            text = path.read_text(encoding="utf-8", errors="replace")
            match = pattern.search(text)
            self.assertIsNone(
                match, f"{path.relative_to(REPO_ROOT)}: phone number {match and match.group(0)!r}"
            )

    def test_the_tracker_is_not_shipped(self):
        # The tracker names every search the user is in. It is gitignored and
        # created on first use by /apply; a checkout must not contain one, and a
        # working copy that has one must have only the user's own rows in it.
        tracker = REPO_ROOT / "job_search_tracker.csv"
        self.assertTrue(git_ignores(tracker), "job_search_tracker.csv must be gitignored")

    def test_no_packet_or_document_is_tracked(self):
        # .gitkeep markers give the folders their shape; anything else in them
        # is the user's own material and must not be in the repository.
        for folder in ("documents", "applications"):
            for path in (REPO_ROOT / folder).rglob("*"):
                if path.is_dir() or path.name in (".gitkeep", "README.md"):
                    continue
                with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                    # Present on a working copy, but never committed: the guard
                    # test in test_security_guards covers the ignore rules, so
                    # here we only assert the shipped tree has no surprises.
                    self.assertTrue(
                        git_ignores(path),
                        f"{path.relative_to(REPO_ROOT)} is not covered by .gitignore",
                    )


if __name__ == "__main__":
    unittest.main()
