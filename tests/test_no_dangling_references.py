"""Nothing may point at something this workspace does not have.

Half the value of trimming a template is lost if the prose still tells a user to
run /gmail-sync or read a file that was deleted: an agent following a command
file literally will try, fail, and improvise. These tests read every tracked
text file and check that the things it names exist.
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import REPO_ROOT, shipped_files  # noqa: E402

# Commands and tools removed when this workspace was cut down to academic
# applications. None of them may be mentioned as if it still exists.
REMOVED_COMMANDS = [
    "/gmail-sync", "/notion-sync", "/html-report", "/upskill", "/expand",
    "/add-portal", "/add-template", "/scrape-for-jobs",
]
REMOVED_PATHS = [
    "salary_lookup.py", "tools/verify_pdf.py", "tools/robots_check.py",
    "tools/convert_salary_excel.py", "tools/check_upstream_updates.py",
    "tools/upstream_triage.py", "tools/check_framework_version.py",
    ".agents/", "cover_letters/", "company_research/", "upskill/",
    "08-application-forms.md", "09-web-research.md", "05-cv-templates.md",
    "06-cover-letter-templates.md", "cv/main_example.tex",
]

TEXT_FILES = [
    path
    for path in shipped_files("*.md", ".claude/**/*.md", "templates/*", ".github/**/*")
    if path.suffix in {".md", ".tex", ".yml", ".yaml"}
]

# Paths a file may name that live outside the repository or are created at
# runtime by a command.
RUNTIME_PATHS = {
    "job_scraper/seen_jobs.json",
    "seen_jobs.json",
    "job_search_tracker.csv",
    # Written into a packet by /apply or /outcome, per posting.
    "checklist.md",
    "cv.tex",
    "cover_letter.tex",
    "job_posting.md",
    "references.md",
    "outcome.md",
    # The user's own masters in documents/statements/.
    "research_statement.tex",
    "teaching_statement.tex",
}

# Every file that ships, by bare name, for resolving unqualified references.
# Built from shipped_files so a user's gitignored documents/ and applications/
# can never satisfy a reference by accident - CI has neither.
SHIPPED_NAMES = {path.name for path in shipped_files("**/*")} | {
    f"{path.parent.name}/" for path in shipped_files("**/*")
}


def read(path):
    return path.read_text(encoding="utf-8")


class RemovedThingsTests(unittest.TestCase):
    def test_no_removed_command_is_mentioned(self):
        for path in TEXT_FILES:
            if path.name == "CHANGELOG.md":
                continue  # the changelog's job is to say what was removed
            text = read(path)
            for command in REMOVED_COMMANDS:
                with self.subTest(file=path.name, command=command):
                    self.assertNotIn(command, text)

    def test_no_removed_path_is_mentioned(self):
        for path in TEXT_FILES:
            if path.name == "CHANGELOG.md":
                continue  # the changelog's job is to say what was removed
            text = read(path)
            for removed in REMOVED_PATHS:
                with self.subTest(file=path.name, path=removed):
                    self.assertNotIn(removed, text)

    def test_the_removed_files_are_actually_gone(self):
        for removed in REMOVED_PATHS:
            with self.subTest(path=removed):
                self.assertFalse((REPO_ROOT / removed).exists())


class ReferencedPathsExistTests(unittest.TestCase):
    def test_every_backticked_repo_path_resolves(self):
        # Matches `path/like/this.ext` and `path/like/this/` inside backticks.
        pattern = re.compile(r"`([\w./-]+\.(?:md|py|tex|json|csv|yml)|[\w./-]+/)`")
        missing = []
        for path in TEXT_FILES:
            if path.name == "CHANGELOG.md":
                continue  # it names things this release removed
            for match in pattern.finditer(read(path)):
                candidate = match.group(1)
                if candidate in RUNTIME_PATHS or candidate.startswith("<"):
                    continue
                # Placeholders and per-packet paths are written at runtime.
                if any(token in candidate for token in ("<", "[", "*", "example.")):
                    continue
                target = REPO_ROOT / candidate
                if target.exists():
                    continue
                # A bare filename is allowed when a shipped file has that name
                # (profile files are referred to this way).
                if "/" not in candidate.rstrip("/") and candidate in SHIPPED_NAMES:
                    continue
                # Per-packet and per-document artifacts, created by /apply.
                if candidate.startswith(("applications/", "documents/", "cv/", "prep_")):
                    continue
                missing.append(f"{path.relative_to(REPO_ROOT)} -> {candidate}")
        self.assertEqual(missing, [], "referenced paths that do not exist")


class PipelineNamesTests(unittest.TestCase):
    def test_every_command_named_in_the_docs_exists(self):
        commands = {p.stem for p in (REPO_ROOT / ".claude" / "commands").glob("*.md")}
        commands.add("scrape")  # a skill, invoked the same way
        pattern = re.compile(r"[`\s(]/([a-z][a-z-]+)")
        for path in TEXT_FILES:
            if path.name == "CHANGELOG.md":
                continue  # it names the commands this release removed
            for match in pattern.finditer(read(path)):
                name = match.group(1)
                with self.subTest(file=path.name, command=name):
                    self.assertIn(name, commands)


if __name__ == "__main__":
    unittest.main()
