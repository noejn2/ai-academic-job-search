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


class ScanCoverageTests(unittest.TestCase):
    """is_ignored matched an ignored directory name at any depth.

    A nested folder that merely shared a name with a gitignored top-level one
    was treated as the user's own, so every personal-data scan that reads
    shipped_files() skipped it without saying so.
    """

    def test_a_nested_lookalike_directory_is_still_scanned(self):
        import support
        self.assertFalse(support.is_ignored(REPO_ROOT / "templates" / "documents" / "x.md"))
        self.assertFalse(support.is_ignored(REPO_ROOT / "tools" / "applications" / "x.py"))

    def test_the_real_personal_directories_are_still_skipped(self):
        import support
        for path in ("documents/cv/mine.tex", "applications/x_y/cover_letter.tex"):
            with self.subTest(path=path):
                self.assertTrue(support.is_ignored(REPO_ROOT / path))

    def test_a_directory_argument_does_not_crash(self):
        # relative_to(REPO_ROOT) of the root itself has no parts; indexing
        # part[0] raised IndexError where the old code returned False.
        import support
        self.assertFalse(support.is_ignored(REPO_ROOT))

    def test_the_folder_contract_files_are_still_shipped(self):
        import support
        self.assertFalse(support.is_ignored(REPO_ROOT / "documents" / "README.md"))
        self.assertFalse(support.is_ignored(REPO_ROOT / "documents" / "cv" / ".gitkeep"))


class IssueTemplateTests(unittest.TestCase):
    """This tracker is public; the things a user would paste into it are not."""

    TEMPLATES_DIR = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"

    def test_the_templates_ship(self):
        self.assertTrue((self.TEMPLATES_DIR / "bug-report.md").exists())
        self.assertTrue((self.TEMPLATES_DIR / "config.yml").exists())

    def test_the_bug_report_warns_before_the_first_field(self):
        text = (self.TEMPLATES_DIR / "bug-report.md").read_text(encoding="utf-8")
        warning, _, rest = text.partition("## What happened")
        self.assertTrue(rest, "the template has no fields")
        self.assertIn("PUBLIC", warning)
        self.assertIn("gh repo set-default", warning)
        for risk in ("referees", "posting", "tracker row"):
            with self.subTest(risk=risk):
                self.assertIn(risk, warning)


if __name__ == "__main__":
    unittest.main()
