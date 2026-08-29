"""The page counter has to work on what pdflatex actually emits.

The rule it guards is "the cover letter is one page" (06-cover-letter.md). A counter
that returns nothing on a compressed PDF would make that check vacuous rather than
failing loudly, so the compressed case is the one that matters most here.
"""

import subprocess
import sys
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.pdf_pages import page_count  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "tools" / "pdf_pages.py"


def _compressed_pdf(payload: bytes) -> bytes:
    """A PDF whose page tree is only reachable by inflating a stream."""
    blob = zlib.compress(payload)
    return (
        b"%PDF-1.5\n1 0 obj\n<< /Length "
        + str(len(blob)).encode()
        + b" /Filter /FlateDecode >>\nstream\n"
        + blob
        + b"\nendstream\nendobj\n"
    )


class PlainPdfTests(unittest.TestCase):
    def test_reads_count_from_the_page_tree(self):
        self.assertEqual(page_count(b"%PDF-1.4\n<< /Type /Pages /Count 3 >>"), 2 + 1)

    def test_reads_count_when_written_before_type(self):
        self.assertEqual(page_count(b"%PDF-1.4\n<< /Count 7 /Type /Pages >>"), 7)

    def test_root_count_wins_over_a_subtree_count(self):
        data = b"%PDF-1.4\n<< /Type /Pages /Count 2 >>\n<< /Type /Pages /Count 9 >>"
        self.assertEqual(page_count(data), 9)

    def test_falls_back_to_counting_leaf_pages(self):
        data = b"%PDF-1.4\n<< /Type /Page >>\n<< /Type /Page >>\n<< /Type /Page >>"
        self.assertEqual(page_count(data), 3)

    def test_pages_node_is_not_counted_as_a_leaf(self):
        # /Type /Page(?![a-zA-Z]) must not match "/Type /Pages".
        data = b"%PDF-1.4\n<< /Type /Pages >>\n<< /Type /Page >>"
        self.assertEqual(page_count(data), 1)

    def test_rejects_a_file_that_is_not_a_pdf(self):
        with self.assertRaises(ValueError):
            page_count(b"just some text\n")

    def test_rejects_a_pdf_with_no_pages_at_all(self):
        with self.assertRaises(ValueError):
            page_count(b"%PDF-1.4\n<< /Type /Catalog >>")


class CompressedPdfTests(unittest.TestCase):
    """pdflatex hides the page tree in a FlateDecode object stream."""

    def test_counts_a_page_tree_inside_an_object_stream(self):
        self.assertEqual(page_count(_compressed_pdf(b"<< /Type /Pages /Count 4 >>")), 4)

    def test_counts_leaf_pages_inside_an_object_stream(self):
        payload = b"<< /Type /Page /MediaBox [0 0 612 792] >>" * 2
        self.assertEqual(page_count(_compressed_pdf(payload)), 2)

    def test_a_stream_that_does_not_inflate_is_skipped_not_fatal(self):
        data = (
            b"%PDF-1.5\n<< /Type /Pages /Count 1 >>\n"
            b"1 0 obj\nstream\n\x00\x01\x02not-zlib\nendstream\nendobj\n"
        )
        self.assertEqual(page_count(data), 1)


class CliTests(unittest.TestCase):
    def test_usage_error_without_an_argument(self):
        result = subprocess.run(
            [sys.executable, str(TOOL)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 2)

    def test_missing_file_exits_one_and_says_so(self):
        result = subprocess.run(
            [sys.executable, str(TOOL), str(REPO_ROOT / "nope.pdf")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("nope.pdf", result.stderr)

    def test_prints_the_count_for_a_real_file(self):
        pdf = REPO_ROOT / "tests" / "fixtures" / "one_page.pdf"
        pdf.write_bytes(_compressed_pdf(b"<< /Type /Pages /Count 1 >>"))
        try:
            result = subprocess.run(
                [sys.executable, str(TOOL), str(pdf)], capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "1")
        finally:
            pdf.unlink()


if __name__ == "__main__":
    unittest.main()
