"""The board fetcher's parsers, against trimmed captures of the real boards.

Boards change their markup. When one does, the parser breaks silently: it
returns an empty list and /scrape reports a quiet sweep. These fixtures are what
turns that into a failing test. Each is two real listings, trimmed by hand -
never a full board dump.
"""

import argparse
import contextlib
import email.message
import io
import json
import subprocess
import sys
import unittest
import unittest.mock
import urllib.error
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools import boards  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"

SHEET_NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'


def build_joe_xlsx(rows):
    """Build the smallest .xlsx the JOE parser must read.

    The real export is a shared-strings workbook: cells hold indices into
    xl/sharedStrings.xml, and empty cells are self-closing. Both shapes are
    reproduced here, because both are where a naive parser goes wrong - a
    regex that misses a self-closing cell shifts every later column by one.
    """
    shared, indices = [], []
    for row in rows:
        row_indices = []
        for value in row:
            if value == "":
                row_indices.append(None)
                continue
            if value not in shared:
                shared.append(value)
            row_indices.append(shared.index(value))
        indices.append(row_indices)

    strings = "".join(f"<si><t>{value}</t></si>" for value in shared)
    shared_xml = f'<?xml version="1.0"?><sst {SHEET_NS}>{strings}</sst>'

    xml_rows = []
    for number, row in enumerate(indices, start=1):
        cells = []
        for position, index in enumerate(row):
            reference = f"{chr(65 + position)}{number}"
            if index is None:
                cells.append(f'<c r="{reference}"/>')
            else:
                cells.append(f'<c r="{reference}" t="s"><v>{index}</v></c>')
        xml_rows.append(f'<row r="{number}">{"".join(cells)}</row>')
    sheet_xml = (
        f'<?xml version="1.0"?><worksheet {SHEET_NS}><sheetData>'
        f'{"".join(xml_rows)}</sheetData></worksheet>'
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", shared_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buffer.getvalue()


JOE_HEADER = [
    "joe_issue_ID", "jp_id", "jp_section", "jp_institution", "jp_division",
    "jp_department", "jp_keywords", "jp_title", "jp_full_text", "jp_salary_range",
    "jp_agency_insertion_num", "locations", "JEL_Classifications",
    "Application_deadline", "Date_Active",
]
JOE_ACADEMIC = [
    "", "111477552", "US: Full-Time Academic (Permanent, Tenure Track or Tenured)",
    "California Polytechnic State University", "", "Agribusiness",
    "Agricultural Economics\nApplied Econometrics",
    "Assistant/Associate Professor, Agricultural Economics",
    "The Agribusiness Department invites applications...", "", "",
    "UNITED STATES California San Luis Obispo", "Q1 - Agriculture",
    "2026-10-02 00:00:00", "2026-08-06 00:00:00",
]
JOE_NONACADEMIC = [
    "", "111477663", "Full-Time Nonacademic", "America First Policy Institute", "",
    "Office for Fiscal and Regulatory Analysis", "Public Finance",
    "Research Engineer", "Overall responsibility...", "", "", "UNITED STATES",
    "H1 - Structure and Scope of Government", "2027-01-31 00:00:00",
    "2026-08-14 00:00:00",
]


class JoeParserTests(unittest.TestCase):
    def setUp(self):
        payload = build_joe_xlsx([JOE_HEADER, JOE_ACADEMIC, JOE_NONACADEMIC])
        self.rows = boards.parse_joe(payload)

    def test_every_column_lands_in_the_right_field(self):
        row = self.rows[0]
        self.assertEqual(row["id"], "joe-111477552")
        self.assertEqual(row["title"], "Assistant/Associate Professor, Agricultural Economics")
        self.assertEqual(row["institution"], "California Polytechnic State University")
        self.assertEqual(row["department"], "Agribusiness")
        self.assertEqual(row["deadline"], "2026-10-02")
        self.assertEqual(row["posted"], "2026-08-06")
        self.assertIn("Tenure Track", row["appointment"])
        self.assertIn("Agricultural Economics", row["field"])
        self.assertIn("Agribusiness Department", row["description"])

    def test_url_is_built_from_the_posting_id(self):
        # The export leaves joe_issue_ID empty, so the listing URL cannot be
        # assembled from the issue. The bare posting id redirects to the
        # canonical listing, which is why this form is used.
        self.assertEqual(
            self.rows[0]["url"],
            "https://www.aeaweb.org/joe/listing.php?JOE_ID=111477552",
        )

    def test_academic_filter_uses_the_section_label(self):
        self.assertTrue(boards.is_academic(self.rows[0]))
        self.assertFalse(boards.is_academic(self.rows[1]))

    def test_a_corrupt_export_is_an_error_not_an_empty_sweep(self):
        with self.assertRaises(boards.BoardError):
            boards.parse_joe(b"not a spreadsheet")


class EjmParserTests(unittest.TestCase):
    def setUp(self):
        self.rows = boards.parse_ejm((FIXTURES / "ejm_positions.html").read_bytes())

    def test_both_listings_are_found(self):
        # The fixture holds one featured listing (wrapped in a "card" div) and
        # one plain row. Splitting on the card wrapper finds only the first,
        # which is how four fifths of the board went missing once already.
        self.assertEqual(len(self.rows), 2)

    def test_fields(self):
        row = self.rows[0]
        self.assertEqual(row["id"], "ejm-12554")
        self.assertEqual(row["url"], "https://econjobmarket.org/positions/12554")
        self.assertEqual(row["title"], "Assistant/Associate Professor")
        self.assertEqual(row["institution"], "Simon Fraser University")
        self.assertEqual(row["department"], "Department of Economics")
        self.assertEqual(row["location"], "Burnaby, Canada")
        self.assertEqual(row["posted"], "2026-08-18")
        self.assertEqual(row["deadline"], "2026-10-01")
        self.assertIn("Assistant Professor", row["appointment"])
        # The appointment column ends at the separator; the fields that follow
        # it belong in `field`, not in the appointment type.
        self.assertNotIn("Econometrics", row["appointment"])
        self.assertIn("Econometrics", row["field"])
        self.assertIn("Simon Fraser University", row["description"])

    def test_the_deadline_is_read_from_the_right_span(self):
        # Listings carry three or four date spans. The application deadline is
        # the "positive" span when there is one and the "negative" closing date
        # otherwise; taking a fixed position gets one of the two shapes wrong.
        self.assertEqual(
            [(row["posted"], row["deadline"]) for row in self.rows],
            [("2026-08-18", "2026-10-01"), ("2026-05-15", "2026-11-30")],
        )


class AaeaParserTests(unittest.TestCase):
    def setUp(self):
        self.rows = boards.parse_aaea((FIXTURES / "aaea_jobboard.html").read_bytes())

    def test_both_adverts_are_found(self):
        self.assertEqual(len(self.rows), 2)

    def test_fields(self):
        row = next(r for r in self.rows if "Arizona" in r["institution"])
        self.assertEqual(row["title"], "Lead Economist, EBRC")
        self.assertEqual(row["institution"], "The University of Arizona")
        self.assertEqual(row["location"], "Tucson, Arizona, United States")
        self.assertEqual(row["posted"], "2026-08-20")
        self.assertTrue(row["url"].startswith("https://aaea.execinc.com/"))
        self.assertTrue(row["id"].startswith("aaea-"))

    def test_the_board_publishes_no_deadline(self):
        # Recorded deliberately: /rank must not read an empty deadline as "no
        # deadline exists", and the scrape skill fetches the posting page.
        self.assertEqual([row["deadline"] for row in self.rows], ["", ""])


class DateTests(unittest.TestCase):
    def test_every_shape_the_three_boards_emit(self):
        cases = {
            "2027-01-31 00:00:00": "2027-01-31",
            "2026-08-06": "2026-08-06",
            "1 Oct 2026": "2026-10-01",
            "18 Aug 2026": "2026-08-18",
            "08/20/2026": "2026-08-20",
            "": "",
            "Open until filled": "",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(boards.iso_date(raw), expected)


class RecordShapeTests(unittest.TestCase):
    def test_every_parser_returns_the_same_keys_with_string_values(self):
        payloads = {
            "joe": build_joe_xlsx([JOE_HEADER, JOE_ACADEMIC]),
            "ejm": (FIXTURES / "ejm_positions.html").read_bytes(),
            "aaea": (FIXTURES / "aaea_jobboard.html").read_bytes(),
        }
        for board, payload in payloads.items():
            for row in boards.PARSERS[board](payload):
                with self.subTest(board=board):
                    self.assertEqual(set(row), set(boards.FIELDS))
                    self.assertTrue(all(isinstance(v, str) for v in row.values()))
                    self.assertEqual(row["board"], board)
                    # Downstream dedup keys on the URL, so it can never be empty.
                    self.assertTrue(row["url"])

    def test_every_board_has_a_parser_and_a_url(self):
        self.assertEqual(set(boards.BOARDS), set(boards.PARSERS))
        self.assertEqual(set(boards.BOARDS), set(boards.URLS))


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "boards.py"), *args],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )

    def test_json_output_is_parseable_and_filtered(self):
        result = self.run_cli(
            "--board", "aaea", "--fixture", str(FIXTURES / "aaea_jobboard.html"),
            "--query", "arizona",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["meta"]["count"], 1)
        self.assertEqual(payload["meta"]["boards"], ["aaea"])
        self.assertIn("Arizona", payload["results"][0]["institution"])

    def test_table_output_names_every_posting(self):
        result = self.run_cli(
            "--board", "ejm", "--fixture", str(FIXTURES / "ejm_positions.html"),
            "--format", "table",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Simon Fraser University", result.stdout)

    def test_a_fixture_needs_a_single_board(self):
        result = self.run_cli("--fixture", str(FIXTURES / "aaea_jobboard.html"))
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()


class ParserIsolationTests(unittest.TestCase):
    """One board failing never aborts the others - BoardError's own promise.

    Only `fetch` and the XLSX reader raised BoardError. A parser reads live
    markup, so a ParseError or KeyError from a changed board walked straight
    past main's handler and `--board all` lost every board.
    """

    def test_a_parser_blowing_up_becomes_a_board_error(self):
        with unittest.mock.patch.dict(
            boards.PARSERS, {"joe": lambda payload: (_ for _ in ()).throw(KeyError("column"))}
        ):
            with self.assertRaises(boards.BoardError):
                boards.parse("joe", b"")

    def test_a_board_error_is_not_double_wrapped(self):
        original = boards.BoardError("already reported")
        with unittest.mock.patch.dict(
            boards.PARSERS, {"joe": lambda payload: (_ for _ in ()).throw(original)}
        ):
            with self.assertRaises(boards.BoardError) as caught:
                boards.parse("joe", b"")
        self.assertIs(caught.exception, original)

    def test_the_other_boards_still_return_when_one_parser_breaks(self):
        def broken(payload):
            raise ValueError("markup changed")

        stdout = io.StringIO()
        with unittest.mock.patch.dict(boards.PARSERS, {"joe": broken}), \
             unittest.mock.patch.object(
                 boards, "fetch",
                 lambda url: (FIXTURES / "ejm_positions.html").read_bytes()), \
             contextlib.redirect_stdout(stdout):
            code = boards.main(["--board", "all", "--format", "json"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertTrue(payload["results"], "a broken parser emptied the whole sweep")
        self.assertTrue(any("joe" in problem for problem in payload["meta"]["errors"]))


class LimitFlagTests(unittest.TestCase):
    """`--limit 0` read as "no limit" and `--limit -1` silently dropped a row."""

    def test_a_non_positive_limit_is_refused(self):
        for value in ("0", "-1"):
            with self.subTest(value=value):
                with self.assertRaises(argparse.ArgumentTypeError):
                    boards._positive(value)

    def test_a_positive_limit_is_accepted(self):
        self.assertEqual(boards._positive("3"), 3)


class RetryTests(unittest.TestCase):
    """A board answering 429 or 503 is busy, not unreadable."""

    def _fetch_returning(self, responses):
        calls = []

        def fake_urlopen(request, timeout=None):
            calls.append(request.full_url)
            outcome = responses[len(calls) - 1]
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        return fake_urlopen, calls

    @staticmethod
    def _ok(body=b"payload"):
        response = unittest.mock.MagicMock()
        response.read.return_value = body
        response.headers.get.return_value = None
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        return response

    @staticmethod
    def _http(code):
        return urllib.error.HTTPError("http://b", code, "busy", email.message.Message(), None)

    def test_a_transient_status_is_retried_then_succeeds(self):
        fake, calls = self._fetch_returning([self._http(503), self._ok()])
        with unittest.mock.patch.object(boards.urllib.request, "urlopen", fake), \
             unittest.mock.patch.object(boards.time, "sleep") as slept:
            self.assertEqual(boards.fetch("http://b"), b"payload")
        self.assertEqual(len(calls), 2)
        slept.assert_called_once()

    def test_a_permanent_status_is_not_retried(self):
        fake, calls = self._fetch_returning([self._http(404)])
        with unittest.mock.patch.object(boards.urllib.request, "urlopen", fake), \
             unittest.mock.patch.object(boards.time, "sleep"):
            with self.assertRaises(boards.BoardError):
                boards.fetch("http://b")
        self.assertEqual(len(calls), 1, "a 404 was retried")

    def test_a_dead_host_fails_fast(self):
        # Retrying a refused connection just delays the report.
        fake, calls = self._fetch_returning([urllib.error.URLError("refused")])
        with unittest.mock.patch.object(boards.urllib.request, "urlopen", fake), \
             unittest.mock.patch.object(boards.time, "sleep"):
            with self.assertRaises(boards.BoardError):
                boards.fetch("http://b")
        self.assertEqual(len(calls), 1)

    def test_retries_are_bounded(self):
        fake, calls = self._fetch_returning([self._http(429)] * boards.RETRIES)
        with unittest.mock.patch.object(boards.urllib.request, "urlopen", fake), \
             unittest.mock.patch.object(boards.time, "sleep"):
            with self.assertRaises(boards.BoardError):
                boards.fetch("http://b")
        self.assertEqual(len(calls), boards.RETRIES)

    def test_a_sane_retry_after_is_honoured_and_an_absurd_one_is_capped(self):
        for header, expected in (("5", 5.0), ("99999", 30.0), ("Wed, 21 Oct 2026 07:28:00 GMT", None)):
            with self.subTest(header=header):
                error = self._http(429)
                error.headers["Retry-After"] = header
                fake, _ = self._fetch_returning([error, self._ok()])
                with unittest.mock.patch.object(boards.urllib.request, "urlopen", fake), \
                     unittest.mock.patch.object(boards.time, "sleep") as slept:
                    boards.fetch("http://b")
                delay = slept.call_args[0][0]
                if expected is None:
                    self.assertEqual(delay, boards.BACKOFF)  # fell back to backoff
                else:
                    self.assertEqual(delay, expected)
