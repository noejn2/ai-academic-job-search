"""The LaTeX skeletons a packet is built from.

These files are copied into every application and compiled unattended. A broken
one fails at the worst moment - the night before a deadline - so the shape they
must keep is pinned here, and CI compiles them for real.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = REPO_ROOT / "templates"
PROFILE = REPO_ROOT / ".claude" / "skills" / "job-application-assistant"

DOCUMENTS = ["statement.tex", "cover_letter.tex"]


def read(path):
    return path.read_text(encoding="utf-8")


class TemplateShapeTests(unittest.TestCase):
    def test_the_shipped_set(self):
        self.assertEqual(
            sorted(p.name for p in TEMPLATES.glob("*.tex")),
            ["cover_letter.tex", "preamble.tex", "statement.tex"],
        )

    def test_no_cv_template_ships(self):
        # The CV is the user's own file. A shipped CV template would invite
        # re-keying a record that already exists, and lose its formatting.
        self.assertFalse(list(TEMPLATES.glob("*cv*")))
        self.assertFalse((REPO_ROOT / "cv").exists())

    def test_every_document_shares_the_packet_preamble(self):
        for name in DOCUMENTS:
            with self.subTest(file=name):
                text = read(TEMPLATES / name)
                self.assertIn(r"\input{preamble}", text)
                self.assertIn(r"\documentclass[11pt]{article}", text)

    def test_the_preamble_is_a_fragment_not_a_document(self):
        text = read(TEMPLATES / "preamble.tex")
        self.assertNotIn(r"\documentclass", text)
        self.assertNotIn(r"\begin{document}", text)

    def test_the_preamble_defines_the_header_macro_the_statements_use(self):
        self.assertIn(r"\newcommand{\hdr}[2]", read(TEMPLATES / "preamble.tex"))
        for name in DOCUMENTS:
            if name == "statement.tex":
                self.assertIn(r"\hdr{", read(TEMPLATES / name))

    def test_only_pdflatex_packages_are_used(self):
        # fontspec, xltxtra and xunicode need xelatex or lualatex. The whole
        # packet compiles with pdflatex, and CI installs nothing more.
        text = " ".join(read(p) for p in TEMPLATES.glob("*.tex"))
        for package in ("fontspec", "xltxtra", "xunicode", "moderncv", "cover.cls"):
            with self.subTest(package=package):
                self.assertNotIn(package, text)

    def test_balanced_braces(self):
        for path in TEMPLATES.glob("*.tex"):
            with self.subTest(file=path.name):
                text = re.sub(r"(?<!\\)%.*", "", read(path))
                self.assertEqual(
                    text.count("{") - text.count(r"\{"),
                    text.count("}") - text.count(r"\}"),
                    f"{path.name}: unbalanced braces",
                )

    def test_no_bracket_follows_a_line_break(self):
        r"""`\\` on one line and `[PLACEHOLDER]` on the next is a fatal compile
        error: LaTeX reads the bracket as \\'s optional length argument and stops
        with "Missing number, treated as zero". Every placeholder that follows a
        line break must be braced.
        """
        for path in TEMPLATES.glob("*.tex"):
            with self.subTest(file=path.name):
                text = re.sub(r"(?<!\\)%.*", "", read(path))
                # `\\[12pt]` is a real optional length and is fine; anything
                # else in that bracket is being read as one by mistake.
                self.assertIsNone(
                    re.search(
                        r"\\\\\s*\[(?!\s*[\d.]+\s*"
                        r"(?:pt|mm|cm|in|em|ex|baselineskip|\\baselineskip)\s*\])",
                        text,
                    ),
                    f"{path.name}: a bracket follows a line break unbraced",
                )

    def test_no_unbraced_bracket_item(self):
        # `\item[` with an unbraced argument silently eats the text after it.
        # Checked in the .tex files themselves, and in any LaTeX the guidance
        # files show inside a fenced block - but not in prose, where
        # 05-cv-tailoring.md names the mistake in order to forbid it.
        sources = {path: read(path) for path in TEMPLATES.glob("*.tex")}
        for path in PROFILE.glob("*.md"):
            fenced = re.findall(r"```[a-z]*\n(.*?)```", read(path), re.S)
            if fenced:
                sources[path] = "\n".join(fenced)
        for path, text in sources.items():
            with self.subTest(file=path.name):
                self.assertIsNone(re.search(r"\\item\s*\[", text), f"{path.name}")


class GuidanceTests(unittest.TestCase):
    def test_the_escape_rules_are_documented_where_drafts_are_written(self):
        guidance = read(PROFILE / "05-cv-tailoring.md") + read(PROFILE / "06-cover-letter.md")
        for escape in (r"\&", r"\%", r"\$", r"\#", r"\_"):
            with self.subTest(escape=escape):
                self.assertIn(escape, guidance)

    def test_compiling_twice_is_stated_everywhere_a_pdf_is_produced(self):
        for path in (
            PROFILE / "05-cv-tailoring.md",
            PROFILE / "06-cover-letter.md",
            REPO_ROOT / ".claude" / "commands" / "apply.md",
            TEMPLATES / "README.md",
            TEMPLATES / "preamble.tex",
        ):
            with self.subTest(file=path.name):
                self.assertRegex(read(path), r"(?i)twice")

    def test_the_templates_readme_says_where_the_cv_comes_from(self):
        text = read(TEMPLATES / "README.md")
        self.assertIn("no CV template", text)
        self.assertIn("documents/cv/", text)


if __name__ == "__main__":
    unittest.main()
