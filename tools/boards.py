#!/usr/bin/env python3
"""Fetch academic job postings from the boards that publish them as plain HTTP.

Three boards are supported, chosen because they cover the economics and
agricultural/applied-economics market and serve complete, server-rendered
listings to a plain client:

  joe   AEA JOE Listings      https://www.aeaweb.org/joe/listings
        Read through the board's own spreadsheet export, which carries the full
        posting text, the application deadline and the section label
        ("US: Full-Time Academic (Permanent, Tenure Track or Tenured)", ...).
  ejm   EconJobMarket         https://econjobmarket.org/positions
  aaea  AAEA Job Board        https://aaea.execinc.com/edibo/JobBoard

Boards that need a browser (HigherEdJobs) or that span every discipline
(AcademicJobsOnline, Chronicle Vitae, Interfolio, university HR portals) are
reached with WebSearch `site:` queries instead - see
`.claude/skills/job-scraper/search-queries.md`.

Usage
    python3 tools/boards.py --board all --query "agricultural" --format table
    python3 tools/boards.py --board joe --academic-only --format json

Every board returns the same record shape:

    {"id", "board", "title", "institution", "department", "location",
     "url", "posted", "deadline", "appointment", "field", "description"}

Missing values are empty strings, never null, so downstream consumers can treat
every field as text. Standard library only.

A board answering 429 or 5xx is retried with a widening pause; a refused
connection is not. Any parser failure is reported as a BoardError against that
one board, so `--board all` never loses the boards that did answer.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import html as _html
import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

USER_AGENT = (
    "ai-academic-job-search/1.0 (job seeker's own application assistant; "
    "one request per board per run)"
)
TIMEOUT = 45

JOE_XLSX_URL = "https://www.aeaweb.org/joe/resultset_xls_output.php?mode=xls_xml"
JOE_LISTING_URL = "https://www.aeaweb.org/joe/listing.php?JOE_ID={}"
EJM_URL = "https://econjobmarket.org/positions"
AAEA_URL = "https://aaea.execinc.com/edibo/JobBoard"

BOARDS = ("joe", "ejm", "aaea")
FIELDS = (
    "id",
    "board",
    "title",
    "institution",
    "department",
    "location",
    "url",
    "posted",
    "deadline",
    "appointment",
    "field",
    "description",
)


class BoardError(Exception):
    """A board could not be read. One board failing never aborts the others."""


# --------------------------------------------------------------------------- #
# fetching and small text helpers
# --------------------------------------------------------------------------- #


# A board answering 429 or 5xx is busy, not unreadable. Three tries with a
# widening pause costs at most ~6s and saves the whole board for the sweep.
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
RETRIES = 3
BACKOFF = 2.0


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"}
    )
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                payload = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    payload = gzip.decompress(payload)
                return payload
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRY_STATUSES or attempt == RETRIES:
                raise BoardError(f"{url}: {exc}") from exc
            _pause(exc.headers.get("Retry-After"), attempt)
        except (urllib.error.URLError, OSError) as exc:
            # Connection refused, DNS failure, timeout: the host is not
            # answering. Retrying a dead host just delays the report.
            raise BoardError(f"{url}: {exc}") from exc
    raise BoardError(f"{url}: gave up after {RETRIES} attempts")


def _pause(retry_after: str | None, attempt: int) -> None:
    """Honour Retry-After when the board sends a sane one, else back off."""
    delay = BACKOFF * attempt
    if retry_after:
        try:
            delay = min(max(float(retry_after), 0.0), 30.0)
        except ValueError:
            pass  # an HTTP-date Retry-After; the backoff below is good enough
    time.sleep(delay)


def strip_tags(fragment: str) -> str:
    """HTML fragment to readable text, with comments and scripts removed."""
    fragment = re.sub(r"<!--.*?-->", " ", fragment, flags=re.S)
    fragment = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", fragment)
    fragment = re.sub(r"(?i)<br\s*/?>", "\n", fragment)
    fragment = re.sub(r"(?i)</p\s*>", "\n", fragment)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    text = _html.unescape(fragment).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return "\n".join(line.strip() for line in text.split("\n")).strip()


def one_line(fragment: str) -> str:
    return " ".join(strip_tags(fragment).split())


_MONTHS = {
    m: i
    for i, m in enumerate(
        "jan feb mar apr may jun jul aug sep oct nov dec".split(), start=1
    )
}


def iso_date(value: str) -> str:
    """Normalise the date shapes these three boards emit to YYYY-MM-DD."""
    value = (value or "").strip()
    if not value:
        return ""
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", value)  # 2027-01-31 00:00:00
    if match:
        return "-".join(match.groups())
    match = re.match(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*\s+(\d{4})", value)  # 1 Oct 2026
    if match:
        day, month, year = match.groups()
        number = _MONTHS.get(month.lower())
        if number:
            return f"{year}-{number:02d}-{int(day):02d}"
    match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", value)  # 08/20/2026
    if match:
        month, day, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    return ""


def record(**values) -> dict:
    row = {field: "" for field in FIELDS}
    row.update({k: (v or "").strip() for k, v in values.items() if k in FIELDS})
    return row


# --------------------------------------------------------------------------- #
# AEA JOE - spreadsheet export
# --------------------------------------------------------------------------- #

_SHEET_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def parse_joe(payload: bytes) -> list[dict]:
    """Parse the JOE .xlsx export into records.

    Columns, in order: joe_issue_ID, jp_id, jp_section, jp_institution,
    jp_division, jp_department, jp_keywords, jp_title, jp_full_text,
    jp_salary_range, jp_agency_insertion_num, locations, JEL_Classifications,
    Application_deadline, Date_Active.
    """
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
        shared_xml = archive.read("xl/sharedStrings.xml")
        sheet_xml = archive.read("xl/worksheets/sheet1.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise BoardError(f"JOE export is not a readable spreadsheet: {exc}") from exc

    shared: list[str] = []
    for item in ET.fromstring(shared_xml).findall(f"{_SHEET_NS}si"):
        shared.append("".join(node.text or "" for node in item.iter(f"{_SHEET_NS}t")))

    rows: list[list[str]] = []
    for row_node in ET.fromstring(sheet_xml).iter(f"{_SHEET_NS}row"):
        cells: dict[int, str] = {}
        for cell in row_node.findall(f"{_SHEET_NS}c"):
            reference = cell.get("r", "")
            letters = re.match(r"([A-Z]+)", reference)
            if not letters:
                continue
            index = 0
            for character in letters.group(1):
                index = index * 26 + (ord(character) - 64)
            value_node = cell.find(f"{_SHEET_NS}v")
            if value_node is None or value_node.text is None:
                continue
            value = value_node.text
            if cell.get("t") == "s":
                position = int(value)
                value = shared[position] if position < len(shared) else ""
            cells[index - 1] = value
        if cells:
            width = max(cells) + 1
            rows.append([cells.get(i, "") for i in range(width)])

    if not rows:
        return []

    def column(row: list[str], index: int) -> str:
        return row[index] if index < len(row) else ""

    results = []
    for row in rows[1:]:  # row 0 is the header
        posting_id = column(row, 1)
        if not posting_id:
            continue
        results.append(
            record(
                id=f"joe-{posting_id}",
                board="joe",
                title=column(row, 7),
                institution=column(row, 3),
                department=column(row, 5) or column(row, 4),
                location=column(row, 11),
                url=JOE_LISTING_URL.format(posting_id),
                posted=iso_date(column(row, 14)),
                deadline=iso_date(column(row, 13)),
                appointment=column(row, 2),
                field=" ".join(column(row, 6).split()),
                description=column(row, 8),
            )
        )
    return results


# --------------------------------------------------------------------------- #
# EconJobMarket - listing page
# --------------------------------------------------------------------------- #


def parse_ejm(payload: bytes) -> list[dict]:
    """Parse the EconJobMarket listing page.

    Records are split on the title anchor, not on a wrapper class: only
    featured advertisements sit inside `<div class="card">`, and splitting on
    that silently drops the other four fifths of the page.
    """
    page = payload.decode("utf-8", "replace")
    page = re.sub(r"<!--\[if (?:BLOCK|ENDBLOCK)\]><!\[endif\]-->", "", page)

    anchors = list(re.finditer(r'<a[^>]*id="title-(\d+)"[^>]*>(.*?)</a>', page, re.S))
    results = []
    for position, anchor in enumerate(anchors):
        identifier = anchor.group(1)
        stop = anchors[position + 1].start() if position + 1 < len(anchors) else len(page)
        block = page[anchor.end():stop]

        # The block opens still inside the title's own cell, which continues
        # "<location> (map). Starts <date>."; the remaining columns follow.
        head, _, rest = block.partition('<div class="col-md-')
        columns = re.findall(
            r'<div class="col-md-\d+">(.*?)(?=<div class="col-md-\d+">|\Z)',
            '<div class="col-md-' + rest,
            re.S,
        )
        head = one_line(head)
        location = re.split(r"[.(]", head.replace("(map)", ""), maxsplit=1)[0].strip(" .,")
        institution_lines = [
            line for line in strip_tags(columns[0]).splitlines() if line
        ] if columns else []

        # Date column: posted (bg-info), then the application deadline - the
        # "positive" span where a board shows one, otherwise the "negative"
        # closing date. Listings carry three or four of these.
        spans = re.findall(r'<span[^>]*(?:class="([^"]*)"|style="[^"]*")[^>]*>([^<]+)</span>', block)
        dated = [(cls or "", iso_date(text)) for cls, text in spans]
        dated = [(cls, value) for cls, value in dated if value]
        posted = next((v for c, v in dated if "bg-info" in c), "")
        deadline = next((v for c, v in dated if "positive" in c), "")
        if not deadline:
            deadline = next((v for c, v in dated if "negative" in c), "")

        appointment = ""
        field = ""
        for column in columns[1:]:
            if "type-field-separator" in column or "cats-" in column:
                appointment = one_line(re.split(r"<hr", column)[0])
                categories = re.search(r'id="cats-\d+"[^>]*>(.*?)</div>', column, re.S)
                field = one_line(categories.group(1)) if categories else ""
                break

        body = re.search(r'id="ad-\d+"[^>]*>(.*)', block, re.S)
        results.append(
            record(
                id=f"ejm-{identifier}",
                board="ejm",
                title=one_line(anchor.group(2)),
                institution=institution_lines[-1] if institution_lines else "",
                department=institution_lines[0] if len(institution_lines) > 1 else "",
                location=location,
                url=f"https://econjobmarket.org/positions/{identifier}",
                posted=posted,
                deadline=deadline,
                appointment=appointment,
                field=field,
                description=strip_tags(body.group(1)) if body else "",
            )
        )
    return results


# --------------------------------------------------------------------------- #
# AAEA job board
# --------------------------------------------------------------------------- #


def parse_aaea(payload: bytes) -> list[dict]:
    page = payload.decode("utf-8", "replace")
    results = []
    for advert in re.findall(r'<li class="ad">(.*?)</li>', page, re.S):
        link = re.search(r'href="([^"]+)"', advert)
        title = re.search(r'class="positiontitle">(.*?)</span>', advert, re.S)
        if not link or not title:
            continue
        institution = re.search(r"<strong>(.*?)</strong>", advert, re.S)
        posted = re.search(r'class="topright">(.*?)</div>', advert, re.S)
        identifier = re.search(r"SubmissionId=(\d+)", link.group(1))
        lines = [line for line in strip_tags(advert).splitlines() if line]
        location = ""
        if institution:
            name = one_line(institution.group(1))
            for index, line in enumerate(lines):
                if line == name and index + 1 < len(lines):
                    location = lines[index + 1]
                    break
        results.append(
            record(
                id=f"aaea-{identifier.group(1) if identifier else link.group(1)[-8:]}",
                board="aaea",
                title=one_line(title.group(1)),
                institution=one_line(institution.group(1)) if institution else "",
                location=location,
                url=_html.unescape(link.group(1)),
                posted=iso_date(one_line(posted.group(1))) if posted else "",
            )
        )
    return results


PARSERS = {"joe": parse_joe, "ejm": parse_ejm, "aaea": parse_aaea}
URLS = {"joe": JOE_XLSX_URL, "ejm": EJM_URL, "aaea": AAEA_URL}


# --------------------------------------------------------------------------- #
# filtering and output
# --------------------------------------------------------------------------- #

ACADEMIC_HINTS = (
    "academic",
    "professor",
    "lecturer",
    "faculty",
    "postdoc",
    "post-doc",
    "tenure",
    "instructor",
)


def is_academic(row: dict) -> bool:
    haystack = " ".join(
        (row["appointment"], row["title"], row["institution"], row["department"])
    ).lower()
    if "nonacademic" in haystack.replace(" ", ""):
        return any(hint in row["title"].lower() for hint in ACADEMIC_HINTS)
    return any(hint in haystack for hint in ACADEMIC_HINTS)


def matches(row: dict, queries: list[str]) -> bool:
    if not queries:
        return True
    haystack = " ".join(row[field] for field in FIELDS).lower()
    return any(query.lower() in haystack for query in queries)


def render_table(rows: list[dict]) -> str:
    if not rows:
        return "(no matching postings)"
    lines = []
    for row in rows:
        deadline = row["deadline"] or "-"
        lines.append(
            f"{row['board']:<5} {deadline:<11} {row['institution'][:34]:<34} "
            f"{row['title'][:44]:<44} {row['url']}"
        )
    return "\n".join(lines)


def _positive(value: str) -> int:
    """--limit 0 read as "no limit" and --limit -1 silently dropped the last row."""
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be 1 or more")
    return number


def parse(board: str, payload: bytes) -> list[dict]:
    """Run a board's parser, turning any failure into a BoardError.

    The parsers read live markup and a board can change it without notice.
    Without this, a stray ParseError or KeyError escapes main's handler and
    `--board all` loses every other board too - the one thing BoardError
    promises never happens.
    """
    try:
        return PARSERS[board](payload)
    except BoardError:
        raise
    except Exception as exc:
        raise BoardError(f"parser failed on the response: {exc!r}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--board", default="all", choices=("all",) + BOARDS)
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        help="keep postings matching this term (repeatable, OR-ed)",
    )
    parser.add_argument(
        "--academic-only",
        action="store_true",
        help="drop postings whose section or title is not an academic appointment",
    )
    parser.add_argument("--limit", type=_positive, default=None)
    parser.add_argument("--format", default="json", choices=("json", "table"))
    parser.add_argument(
        "--fixture",
        help="parse this local file instead of fetching (one board only; for tests)",
    )
    args = parser.parse_args(argv)

    boards = BOARDS if args.board == "all" else (args.board,)
    if args.fixture and len(boards) != 1:
        parser.error("--fixture needs a single --board")

    rows: list[dict] = []
    errors: list[str] = []
    for board in boards:
        try:
            if args.fixture:
                with open(args.fixture, "rb") as handle:
                    payload = handle.read()
            else:
                payload = fetch(URLS[board])
            rows.extend(parse(board, payload))
        except BoardError as exc:
            errors.append(f"{board}: {exc}")

    if args.academic_only:
        rows = [row for row in rows if is_academic(row)]
    rows = [row for row in rows if matches(row, args.query)]
    rows.sort(key=lambda row: (row["deadline"] or "9999-99-99", row["institution"]))
    if args.limit is not None:
        rows = rows[: args.limit]

    if args.format == "table":
        print(render_table(rows))
        for problem in errors:
            print(f"warning: {problem}", file=sys.stderr)
    else:
        json.dump(
            {
                "meta": {
                    "boards": list(boards),
                    "count": len(rows),
                    "errors": errors,
                    "fetched": _dt.date.today().isoformat(),
                },
                "results": rows,
            },
            sys.stdout,
            indent=1,
            ensure_ascii=False,
        )
        print()

    if errors and not rows:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
