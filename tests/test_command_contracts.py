"""Contracts between commands.

A command file is a specification an agent follows literally, and several
strings in these files are shared contracts: the tracker header /apply writes
and /outcome reads, the status vocabulary three commands agree on, the compile
instruction that decides whether a PDF has correct page references. When one
copy drifts, nothing crashes - the workspace just starts producing subtly wrong
output. These tests pin the strings that must match.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMANDS = REPO_ROOT / ".claude" / "commands"
SKILLS = REPO_ROOT / ".claude" / "skills"
PROFILE = SKILLS / "job-application-assistant"

TRACKER_HEADER = (
    "date,institution,department,role,appointment,status,fit_rating,"
    "contact_person,notes,packet,source,deadline"
)

OPEN_STATUSES = ["drafted", "applied", "interview", "flyout", "offer"]
FINAL_STATUSES = ["hired", "rejected", "no_response", "offer_declined", "withdrawn"]


def read(path):
    return path.read_text(encoding="utf-8")


def section(text, heading):
    """The body under an exact heading line, up to the next heading.

    Fence-aware: these command files print example output inside ``` blocks,
    and that output contains its own markdown headings. A regex that does not
    track fences ends a section at the first one.
    """
    lines = text.splitlines()
    try:
        start = lines.index(heading.rstrip())
    except ValueError:
        return ""
    body, fenced = [], False
    for line in lines[start + 1:]:
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,4} ", line):
            break
        body.append(line)
    return "\n".join(body)


def flat(text):
    """Collapse whitespace and blockquote markers.

    An assertion about a sentence should not fail because the sentence wraps,
    or because it sits inside a `>` block the command prints to the user.
    """
    lines = [line.lstrip("> ").rstrip() if line.startswith(">") else line
             for line in text.splitlines()]
    return " ".join(" ".join(lines).split())


class PipelineTests(unittest.TestCase):
    def test_exactly_the_expected_commands_ship(self):
        self.assertEqual(
            sorted(p.name for p in COMMANDS.glob("*.md")),
            ["apply.md", "interview.md", "outcome.md", "rank.md", "reset.md", "setup.md"],
        )

    def test_every_command_declares_its_own_name_in_its_title(self):
        for path in COMMANDS.glob("*.md"):
            with self.subTest(command=path.name):
                first = read(path).lstrip().splitlines()[0]
                self.assertTrue(first.startswith(f"# /{path.stem}"), first)

    def test_the_profile_ships_all_nine_reference_files(self):
        names = sorted(p.name for p in PROFILE.glob("*.md"))
        self.assertEqual(
            names,
            [
                "01-candidate-profile.md",
                "02-behavioral-profile.md",
                "03-writing-style.md",
                "04-job-evaluation.md",
                "05-cv-tailoring.md",
                "06-cover-letter.md",
                "07-interview-prep.md",
                "08-statements.md",
                "09-web-research.md",
                "SKILL.md",
            ],
        )


class TrackerTests(unittest.TestCase):
    def test_a_local_tracker_if_present_starts_with_the_header(self):
        # Not shipped (gitignored, created by /apply on first use), but when a
        # working copy has one its first line must be the header the commands
        # agree on, or every column reads shifted.
        tracker = REPO_ROOT / "job_search_tracker.csv"
        if not tracker.exists():
            self.skipTest("no tracker in this checkout - created on first /apply")
        self.assertEqual(read(tracker).splitlines()[0], TRACKER_HEADER)

    def test_apply_and_reset_agree_on_the_header(self):
        # Two copies of one string. /apply creates the file, /reset restores
        # it; a mismatch means a column silently shifts.
        for path in (COMMANDS / "apply.md", COMMANDS / "reset.md"):
            with self.subTest(file=path.name):
                self.assertIn(TRACKER_HEADER, read(path))

    def test_apply_writes_the_packet_path_not_document_paths(self):
        body = section(read(COMMANDS / "apply.md"), "### Tracker")
        self.assertIn("`packet`", body)
        self.assertIn("applications/<institution>_<role>", body)


class StatusVocabularyTests(unittest.TestCase):
    def setUp(self):
        self.outcome = read(COMMANDS / "outcome.md")

    def test_outcome_owns_the_vocabulary(self):
        self.assertIn("## Tracker status vocabulary", self.outcome)

    def test_every_status_is_defined_with_its_finality(self):
        body = section(self.outcome, "## Tracker status vocabulary")
        for status in OPEN_STATUSES + FINAL_STATUSES:
            with self.subTest(status=status):
                self.assertIn(f"`{status}`", body)
        self.assertIn("underscores, never spaces", body)
        for status in FINAL_STATUSES:
            self.assertRegex(flat(body), rf"\*\*Final:\*\*[^.]*{status}")

    def test_the_academic_stages_replaced_the_industry_ones(self):
        # The whole point of the vocabulary change: an academic search runs
        # application -> interview -> flyout -> offer.
        self.assertIn("`flyout`", self.outcome)
        for industry_stage in ("phone screen", "case interview", "final round"):
            with self.subTest(stage=industry_stage):
                self.assertNotIn(industry_stage, self.outcome.lower())

    def test_apply_only_ever_writes_drafted(self):
        body = section(read(COMMANDS / "apply.md"), "### Tracker")
        self.assertIn("`drafted`", body)
        self.assertIn("never overwrite a row whose status is final", flat(body))


class UntrustedInputTests(unittest.TestCase):
    def test_every_command_that_reads_a_posting_states_the_rule(self):
        for name in ("apply.md", "rank.md"):
            with self.subTest(command=name):
                text = read(COMMANDS / name)
                self.assertIn("untrusted", text.lower())
                self.assertRegex(flat(text), r"[Nn]ever fetch a URL")
        skill = read(SKILLS / "job-scraper" / "SKILL.md")
        self.assertIn("untrusted", skill.lower())


class ReferenceLetterTests(unittest.TestCase):
    def test_nothing_in_the_workspace_offers_to_write_one(self):
        # The single rule with no exception anywhere in this repository.
        files = list(COMMANDS.glob("*.md")) + list(PROFILE.glob("*.md")) + [
            REPO_ROOT / "CLAUDE.md",
            REPO_ROOT / "AGENTS.md",
            REPO_ROOT / "documents" / "README.md",
        ]
        stated = [
            path
            for path in files
            if re.search(r"[Nn]ever draft, simulate", read(path))
        ]
        self.assertTrue(stated, "no file states the reference-letter rule")
        for path in (COMMANDS / "setup.md", COMMANDS / "apply.md", REPO_ROOT / "CLAUDE.md"):
            with self.subTest(file=path.name):
                self.assertRegex(read(path), r"[Nn]ever draft, simulate")


class SetupContractTests(unittest.TestCase):
    def setUp(self):
        self.setup = read(COMMANDS / "setup.md")

    def test_privacy_check_runs_before_anything_is_written(self):
        self.assertIn("git remote get-url origin", self.setup)
        self.assertLess(
            self.setup.index("git remote get-url origin"),
            self.setup.index("## Step 7: Write"),
        )

    def test_three_referees_are_required_for_a_complete_profile(self):
        body = section(self.setup, "## Step 3: Referees")
        self.assertIn("**Minimum three.**", body)
        self.assertRegex(
            flat(self.setup), r"at least three referees \*\*and\*\* both statements"
        )
        self.assertIn("Profile status", read(PROFILE / "01-candidate-profile.md"))

    def test_referees_carry_the_fields_a_portal_asks_for(self):
        body = section(self.setup, "## Step 3: Referees")
        for field in ("name", "title", "institution", "email", "phone", "relationship"):
            with self.subTest(field=field):
                self.assertIn(field, body)

    def test_letter_status_is_not_tracked(self):
        # Referees send their own letters; a "letter sent?" column would be a
        # field the user has to maintain and cannot verify.
        self.assertIn("do not track whether a letter has been sent", flat(self.setup))

    def test_statements_are_assessed_not_copied(self):
        body = section(self.setup, "## Step 4: Statements")
        for topic in ("Agenda", "Job market paper", "Pipeline", "Funding record",
                      "Three-to-five year plan", "Philosophy", "Courses taught",
                      "Evaluations", "Courses you can teach"):
            with self.subTest(topic=topic):
                self.assertIn(topic, body)
        self.assertIn("Do not copy the statement text into the profile", flat(body))
        self.assertIn("documents/statements/", body)

    def test_other_statement_types_are_left_to_apply(self):
        self.assertIn("are **not** collected here", flat(read(COMMANDS / "setup.md")))
        apply_text = read(COMMANDS / "apply.md")
        self.assertIn("Other statements - only when the posting names them", apply_text)
        for kind in ("Diversity", "service", "mentoring"):
            with self.subTest(kind=kind):
                self.assertIn(kind, apply_text)

    def test_a_tex_cv_is_required(self):
        body = section(self.setup, "## Step 1: Inventory `documents/`")
        self.assertIn("required", body)
        self.assertIn("A PDF is not enough", flat(body))


class ApplyPacketTests(unittest.TestCase):
    def setUp(self):
        self.apply = read(COMMANDS / "apply.md")

    def test_the_packet_holds_the_whole_application(self):
        for artifact in ("checklist.md", "job_posting.md", "preamble.tex", "cv.tex",
                         "cover_letter.tex", "research_statement.tex",
                         "teaching_statement.tex", "references.md"):
            with self.subTest(artifact=artifact):
                self.assertIn(artifact, self.apply)

    def test_the_required_documents_list_is_quoted_verbatim(self):
        self.assertIn("required documents, quoted verbatim", flat(self.apply))
        self.assertIn("Blocking", self.apply)

    def test_compiles_twice(self):
        # A single pdflatex pass leaves page references and lastpage footers
        # wrong, and the error is invisible in the source.
        self.assertIn("pdflatex -interaction=nonstopmode", self.apply)
        self.assertRegex(self.apply, r"[Tt]wice")

    def test_the_master_documents_are_never_edited(self):
        self.assertIn("Never edit the source file", flat(self.apply))
        self.assertIn("Never edit a master document", flat(read(REPO_ROOT / "CLAUDE.md")))

    def test_no_industry_rules_survive(self):
        # The industry track is gone; these are the rules that would quietly
        # mutilate an academic packet if a fragment of it came back.
        text = self.apply + read(REPO_ROOT / "CLAUDE.md")
        for phrase in ("2 pages", "exactly 2 pages", "ATS parser", "keyword coverage",
                       "moderncv", "cover.cls", "lualatex", "xelatex", "salary"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase.lower(), text.lower())

    def test_the_cv_guidance_names_the_industry_rule_only_to_reject_it(self):
        # 05 may mention the two-page résumé - it explains why the rule does not
        # apply here - but it must never state a page limit as an instruction.
        guidance = read(PROFILE / "05-cv-tailoring.md")
        self.assertIn("exactly wrong here", flat(guidance))
        self.assertIn("no page limit", flat(guidance).lower())

    def test_the_skipped_ats_check_is_reported_not_silently_omitted(self):
        self.assertIn("no ATS or keyword extraction was run", flat(self.apply))


class ScoringTests(unittest.TestCase):
    def test_the_weights_agree_between_the_framework_and_rank(self):
        framework = read(PROFILE / "04-job-evaluation.md")
        rank = read(COMMANDS / "rank.md")
        self.assertIn("0.50*research + 0.30*teaching + 0.20*career", framework)
        self.assertIn("0.50*research + 0.30*teaching + 0.20*career", rank)

    def test_the_gates_are_the_same_four(self):
        framework = read(PROFILE / "04-job-evaluation.md")
        for gate in ("Appointment gate", "Eligibility gate", "Country gate", "Language gate"):
            with self.subTest(gate=gate):
                self.assertIn(gate, framework)

    def test_non_academic_positions_are_out_of_scope_everywhere(self):
        for path in (PROFILE / "04-job-evaluation.md", REPO_ROOT / "CLAUDE.md",
                     SKILLS / "job-scraper" / "SKILL.md"):
            with self.subTest(file=path.name):
                text = read(path).lower()
                self.assertIn("out of scope", text)
                self.assertIn("think tank", text)


class ResetTests(unittest.TestCase):
    def setUp(self):
        self.reset = read(COMMANDS / "reset.md")

    def test_every_personal_folder_is_cleared(self):
        tracked = sorted(
            p.parent.name
            for p in (REPO_ROOT / "documents").glob("*/.gitkeep")
        )
        self.assertTrue(tracked)
        for folder in tracked:
            with self.subTest(folder=folder):
                self.assertIn(f"documents/{folder}/", self.reset)

    def test_every_file_setup_writes_is_reset(self):
        """Derived from /setup, not hardcoded.

        The hardcoded version of this test passed while 03-writing-style.md was
        both written by /setup and listed under /reset's "Not touched" heading:
        a hardcoded tuple cannot notice a file it does not mention, and a
        substring search over the whole file is satisfied by the very heading
        that says the file is skipped. So: read the filenames out of /setup's
        Step 7, and require each inside /reset's reset block specifically.
        """
        written = set(
            re.findall(r"^- `([\w./-]+)`", section(read(COMMANDS / "setup.md"),
                                                   "## Step 7: Write"), re.M)
        )
        self.assertGreaterEqual(len(written), 6, "Step 7's file list did not parse")
        block = section(self.reset, "## Step 1: Show what would go")
        reset_list = block.split("## Files that would be reset to placeholders")[-1]
        reset_list = reset_list.split("## Not touched")[0]
        for target in sorted(written):
            with self.subTest(target=target):
                self.assertIn(
                    Path(target).name, reset_list,
                    f"/setup Step 7 writes {target} but /reset does not clear it",
                )

    def test_nothing_is_both_reset_and_declared_untouched(self):
        block = section(self.reset, "## Step 1: Show what would go")
        reset_list = block.split("## Files that would be reset to placeholders")[-1]
        untouched = reset_list.split("## Not touched")[-1]
        reset_list = reset_list.split("## Not touched")[0]
        names = set(re.findall(r"([\w-]+\.(?:md|tex))", reset_list))
        self.assertTrue(names)
        for name in sorted(names):
            with self.subTest(name=name):
                self.assertNotIn(name, untouched)

    def test_it_confirms_before_deleting(self):
        self.assertLess(self.reset.index("## Step 2: Confirm"), self.reset.index("rm -rf"))
        self.assertIn("cannot be undone", flat(self.reset))


class InterviewTests(unittest.TestCase):
    def test_both_academic_stages_are_prepared(self):
        text = read(COMMANDS / "interview.md")
        self.assertIn("### Interview (first round)", text)
        self.assertIn("### Flyout", text)
        for element in ("Job talk plan", "Teaching demonstration", "One-on-ones"):
            with self.subTest(element=element):
                self.assertIn(element, text)

    def test_prep_must_match_what_was_submitted(self):
        text = read(COMMANDS / "interview.md")
        self.assertIn("must match what was submitted", flat(text))


if __name__ == "__main__":
    unittest.main()


class RobotsGateTests(unittest.TestCase):
    """The browser-header retry may never appear without the check that authorises it.

    The fork shipped for a while with the retry in two command files and the
    robots.txt gate deleted, which turned a documented exception into a blanket
    instruction to spoof a user agent past a 403. These tests make that state fail.
    """

    RETRY_MARKERS = ("Mozilla/5.0", "browser-header retry", "browser headers")

    def _files_mentioning_the_retry(self):
        out = []
        for path in list(COMMANDS.glob("*.md")) + list(SKILLS.glob("*/*.md")):
            text = read(path)
            if any(marker in text for marker in self.RETRY_MARKERS):
                out.append((path, text))
        return out

    # The exact command, not the bare filename. Asserting on "robots_check.py"
    # alone passes on a file that only mentions tests/test_robots_check.py in
    # prose - a mutation that replaced the real invocation went undetected.
    INVOCATION = "python3 tools/robots_check.py"

    def test_the_gate_ships(self):
        self.assertTrue((REPO_ROOT / "tools" / "robots_check.py").is_file())
        self.assertTrue((PROFILE / "09-web-research.md").is_file())

    def test_the_invocation_names_a_tool_that_exists(self):
        text = read(PROFILE / "09-web-research.md")
        self.assertIn(self.INVOCATION, text)
        for match in re.finditer(r"python3 (tools/[\w./-]+\.py)", text):
            with self.subTest(tool=match.group(1)):
                self.assertTrue((REPO_ROOT / match.group(1)).is_file())

    def test_every_file_that_mentions_the_retry_requires_the_check(self):
        found = self._files_mentioning_the_retry()
        self.assertTrue(found, "no file mentions the retry; markers are stale")
        for path, text in found:
            with self.subTest(file=path.name):
                # Either it runs the check itself, or it defers to the one file
                # that does. Nothing may describe the retry without one or the other.
                self.assertTrue(
                    self.INVOCATION in text or "09-web-research.md" in text,
                    f"{path.name} describes the retry without gating it",
                )

    def test_the_rule_is_stated_where_the_command_lives(self):
        text = read(PROFILE / "09-web-research.md")
        self.assertIn("never used to override a site that has said no", flat(text))
        # A failure to read the policy must not be treated as permission.
        self.assertIn("unconfirmed", flat(text))

    def test_the_curl_invocation_has_exactly_one_home(self):
        # Upstream kept it in one file so the callers could not drift. Two
        # verbatim copies is how the gate got dropped from one of them.
        holders = [
            path.name
            for path in list(COMMANDS.glob("*.md")) + list(SKILLS.glob("*/*.md"))
            if "Mozilla/5.0" in read(path)
        ]
        self.assertEqual(holders, ["09-web-research.md"], holders)

    def test_apply_stops_rather_than_drafting_from_a_title(self):
        text = flat(read(COMMANDS / "apply.md"))
        self.assertIn("could not be retrieved and stop", text)


class RankSweepTests(unittest.TestCase):
    def setUp(self):
        self.rank = read(COMMANDS / "rank.md")

    def test_there_is_an_expiry_sweep_over_already_ranked_entries(self):
        self.assertIn("Expiry sweep", self.rank)
        body = flat(section(self.rank, "## Step 3b: Expiry sweep over already-ranked entries"))
        self.assertIn("did not re-score", body)
        # An absent or unparseable deadline is left alone, never guessed at.
        self.assertIn("never guessed at", body)
        self.assertIn("YYYY-MM-DD", body)

    def test_the_sweep_runs_before_the_shortlist_is_presented(self):
        self.assertLess(
            self.rank.index("## Step 3b: Expiry sweep"),
            self.rank.index("## Step 4: Present"),
        )

    def test_the_gate_reason_is_persisted_not_only_displayed(self):
        # /scrape stores `gate`; /rank must agree, or a veto is unrecoverable.
        stored = section(self.rank, "## Step 3: Store")
        self.assertIn("`gate`", stored)
        scrape = read(SKILLS / "job-scraper" / "SKILL.md")
        self.assertIn('"gate"', scrape)

    def test_the_shortlist_keeps_the_posting_url(self):
        # The command ends by telling the user to run `/apply <url>`; a table
        # without the link sends them into seen_jobs.json for the argument.
        present = section(self.rank, "## Step 4: Present")
        self.assertIn("| URL |", present)
        self.assertIn("never drop it for brevity", flat(present).lower())

    def test_stored_posting_derivatives_are_still_untrusted(self):
        self.assertIn("still untrusted data", flat(self.rank))


class SubmissionSnapshotTests(unittest.TestCase):
    """/interview promises to prepare against what was submitted; something must freeze it."""

    def test_outcome_freezes_the_packet_on_submission(self):
        text = flat(read(COMMANDS / "outcome.md"))
        self.assertIn("submitted/", text)
        self.assertIn("Never overwrite an existing", text)

    def test_outcome_corrects_the_draft_date_on_submission(self):
        # /apply writes the draft date; leaving it makes every follow-up
        # calculation run off a date the application was not sent on.
        self.assertIn("submission date", flat(read(COMMANDS / "outcome.md")))

    def test_interview_reads_the_frozen_copy_when_it_exists(self):
        text = flat(read(COMMANDS / "interview.md"))
        self.assertIn("submitted/", text)
        self.assertIn("must match what was submitted", text)

    def test_apply_never_writes_into_the_frozen_copy(self):
        self.assertIn("Never write into `submitted/`", read(COMMANDS / "apply.md"))


class ScrapeOrderingTests(unittest.TestCase):
    def test_gates_run_before_the_per_posting_fetch(self):
        text = read(SKILLS / "job-scraper" / "SKILL.md")
        self.assertLess(text.index("## Step 2: Gates"), text.index("## Step 3: Fetch"))

    def test_the_country_gate_says_how_to_parse_location(self):
        # JOE writes the country first, EJM last. Splitting on a comma and
        # taking one end silently drops every JOE record.
        text = flat(read(SKILLS / "job-scraper" / "SKILL.md"))
        self.assertIn("substring of the whole field", text)
