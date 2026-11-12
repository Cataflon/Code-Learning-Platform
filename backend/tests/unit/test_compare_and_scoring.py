import pytest

from app.models.submission import Verdict
from app.runner.base import RunResult, truncate_output
from app.runner.compare import normalize, outputs_match
from app.services.scoring import compute_score, decide_verdict, extract_error_excerpt
from tests.fakes import crash, ok, out_of_memory, timeout


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        ("10\n", "10"),
        ("10", "10\n"),
        ("10   \n", "10\n"),  # trailing spaces on a line
        ("10\n\n\n", "10\n"),  # trailing blank lines
        ("1\r\n2\r\n", "1\n2\n"),  # Windows line endings
        ("a  b\n", "a  b"),  # inner spaces are kept as they are
        ("", "\n"),
    ],
)
def test_outputs_match_ignores_trailing_whitespace(actual, expected):
    assert outputs_match(actual, expected)


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        ("10", "11"),
        (" 10", "10"),  # leading spaces matter
        ("a b", "a  b"),  # inner spaces matter
        ("1\n\n2", "1\n2"),  # blank lines in the middle matter
        ("ABC", "abc"),
    ],
)
def test_outputs_match_rejects_real_differences(actual, expected):
    assert not outputs_match(actual, expected)


def test_normalize_strips_line_ends_and_trailing_blank_lines():
    assert normalize("a \r\nb\t\n\n \n") == "a\nb"


@pytest.mark.parametrize(
    ("result", "verdict"),
    [
        (ok("10\n"), Verdict.passed),
        (ok("11\n"), Verdict.wrong_answer),
        (crash(), Verdict.runtime_error),
        (timeout(), Verdict.time_limit),
        (out_of_memory(), Verdict.memory_limit),
        # limits win over everything else, even over a correct output
        (RunResult("10\n", "", 0, 10, timed_out=True), Verdict.time_limit),
        # a crash wins over a correct output
        (RunResult("10\n", "boom", 1, 10), Verdict.runtime_error),
    ],
)
def test_decide_verdict(result, verdict):
    assert decide_verdict(result, "10\n") == verdict


def test_compute_score_uses_weights():
    weights = {1: 3, 2: 3, 3: 4}

    assert (
        compute_score({1: Verdict.passed, 2: Verdict.passed, 3: Verdict.wrong_answer}, weights)
        == 60
    )
    assert compute_score({3: Verdict.passed}, weights) == 40


def test_compute_score_bounds():
    weights = {1: 1, 2: 1}

    assert compute_score({}, weights) == 0
    assert compute_score({1: Verdict.time_limit, 2: Verdict.runtime_error}, weights) == 0
    assert compute_score({1: Verdict.passed, 2: Verdict.passed}, weights) == 100
    assert compute_score({}, {}) == 0


def test_extract_error_excerpt_reads_python_traceback():
    stderr = (
        "Traceback (most recent call last):\n"
        '  File "/sandbox/main.py", line 4, in <module>\n'
        "    print(items[5])\n"
        "IndexError: list index out of range\n"
    )

    assert extract_error_excerpt(stderr) == "IndexError, line 4"
    assert extract_error_excerpt("") is None
    assert extract_error_excerpt("Killed") == "Killed"
    assert len(extract_error_excerpt("x" * 500)) == 200


def test_truncate_output_respects_byte_limit_without_breaking_characters():
    assert truncate_output("abc", 10) == "abc"
    assert truncate_output("a" * 100, 10) == "a" * 10
    assert truncate_output("ăăă", 3) == "ă"  # each character is 2 bytes in UTF-8
