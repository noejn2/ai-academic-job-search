#!/usr/bin/env python3
"""Print a PDF's page count.

Exists because two rules in this workspace are page counts and both have to be
checkable without a dependency: the cover letter is one page (06-cover-letter.md),
and /apply Step 6 reads every packet PDF before presenting it. Standard library
only, like everything else in tools/.

pdflatex writes the page tree into a compressed object stream (/ObjStm), so a regex
over the raw bytes finds nothing - the naive version of this tool reported zero pages
for every real packet. Every FlateDecode stream is therefore inflated first and the
search runs over the raw bytes plus the inflated ones.

Reads the page tree's /Count, which is what a viewer uses. Falls back to counting
/Type /Page objects when no tree is found.

Usage:  python3 tools/pdf_pages.py <file.pdf>
Prints the count. Exit 0 on success, 1 if the file is not a readable PDF.
"""

import re
import sys
import zlib

# /Count on a page-tree node, in either dictionary order. The root node's count is
# the document's, and it is the largest: a child node counts only its own subtree.
_TREE = (
    re.compile(rb"/Type\s*/Pages\b[^>]{0,400}?/Count\s+(\d+)"),
    re.compile(rb"/Count\s+(\d+)[^>]{0,400}?/Type\s*/Pages\b"),
)
# \b would match "/Pages" too, so require a non-name character after "Page".
_LEAF = re.compile(rb"/Type\s*/Page(?![a-zA-Z])")


def _inflate_streams(data: bytes) -> list[bytes]:
    """Every stream that inflates, ignoring the ones that do not.

    Image and font streams fail or yield binary; both are harmless here, since the
    patterns above only match a page dictionary.
    """
    out = []
    for match in re.finditer(rb"stream\r?\n", data):
        start = match.end()
        end = data.find(b"endstream", start)
        if end < 0:
            continue
        try:
            out.append(zlib.decompress(data[start:end]))
        except zlib.error:
            continue
    return out


def page_count(data: bytes) -> int:
    if not data.startswith(b"%PDF-"):
        raise ValueError("not a PDF: missing %PDF- header")
    haystacks = [data] + _inflate_streams(data)
    counts = [
        int(n) for blob in haystacks for pattern in _TREE for n in pattern.findall(blob)
    ]
    if counts:
        return max(counts)
    leaves = sum(len(_LEAF.findall(blob)) for blob in haystacks)
    if leaves:
        return leaves
    raise ValueError("no page tree and no page objects found")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 tools/pdf_pages.py <file.pdf>", file=sys.stderr)
        return 2
    try:
        with open(argv[1], "rb") as handle:
            print(page_count(handle.read()))
    except (OSError, ValueError) as exc:
        print(f"{argv[1]}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
