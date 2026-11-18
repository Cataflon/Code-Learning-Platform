import pytest

from app.services.pages import PagesError, first_page, merge_ranges, normalize_pages, parse_pages


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("12-15, 18", [(12, 15), (18, 18)]),
        ("  12 - 15 ,18  ", [(12, 15), (18, 18)]),
        ("18, 12-15", [(12, 15), (18, 18)]),  # sorted
        ("3", [(3, 3)]),
        ("1-2, 2-4, 5", [(1, 5)]),  # overlapping and touching ranges are joined
        ("", []),  # empty = the whole material
        (None, []),
        ("   ", []),
    ],
)
def test_parse_pages_accepts_valid_lists(text, expected):
    assert parse_pages(text, page_count=28) == expected


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("5-3", "backwards"),
        ("0", "start at 1"),
        ("29", "does not exist"),
        ("12-40", "does not exist"),
        ("abc", "not a page"),
        ("12,,15", "not a page"),
        ("1-2-3", "not a page"),
        ("-4", "not a page"),
        ("../etc", "not a page"),
    ],
)
def test_parse_pages_rejects_bad_lists(text, message):
    with pytest.raises(PagesError, match=message):
        parse_pages(text, page_count=28)


def test_normalize_and_first_page():
    assert normalize_pages(" 18 , 12-15", 28) == "12-15, 18"
    assert normalize_pages("4-4", 28) == "4"
    assert first_page("12-15, 18") == 12
    assert first_page("") == 1


def test_merge_ranges():
    assert merge_ranges([(12, 15), (14, 18), (19, 19), (25, 26)]) == [(12, 19), (25, 26)]
