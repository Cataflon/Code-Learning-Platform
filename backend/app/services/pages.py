"""Page lists such as "12-15, 18" (decision D23): parsing, checking, merging. Pure functions."""

import re

_PART = re.compile(r"^(\d+)(?:\s*-\s*(\d+))?$")

Ranges = list[tuple[int, int]]


class PagesError(ValueError):
    pass


def parse_pages(text: str | None, page_count: int) -> Ranges:
    """Turn "12-15, 18" into [(12, 15), (18, 18)]. Empty text means the whole material.

    Pages start at 1, must exist in the document, and a range may not go backwards.
    """
    text = (text or "").strip()
    if not text:
        return []
    ranges = []
    for raw in text.split(","):
        part = raw.strip()
        match = _PART.fullmatch(part)
        if not match:
            raise PagesError(
                f"“{part or raw}” is not a page or a range. Use a format like 12-15, 18"
            )
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if start < 1:
            raise PagesError("Pages start at 1")
        if end < start:
            raise PagesError(f"The range {start}-{end} goes backwards")
        if end > page_count:
            raise PagesError(f"Page {end} does not exist; the material has {page_count} pages")
        ranges.append((start, end))
    return merge_ranges(ranges)


def merge_ranges(ranges: Ranges) -> Ranges:
    """Sort and join overlapping or touching ranges: (12,15),(14,18),(19,19) -> (12,19)."""
    merged: Ranges = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def format_pages(ranges: Ranges) -> str:
    """The normalized form stored in the database: "12-15, 18"; "" = all pages."""
    return ", ".join(f"{a}" if a == b else f"{a}-{b}" for a, b in ranges)


def normalize_pages(text: str | None, page_count: int) -> str:
    return format_pages(parse_pages(text, page_count))


def first_page(text: str | None) -> int:
    """Where a link opens: the first page of the list, or page 1."""
    match = re.search(r"\d+", text or "")
    return int(match.group()) if match else 1
