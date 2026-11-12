"""Pure functions: verdict of one run, score of a submission, error excerpt.

Nothing here touches the database or starts a process, so it is tested exhaustively and fast.
"""

import re
from collections.abc import Iterable, Mapping

from app.models.submission import Verdict
from app.runner.base import RunResult
from app.runner.compare import outputs_match


def decide_verdict(result: RunResult, expected_output: str) -> Verdict:
    """Order matters: limits first, then the exit code, and only then the output."""
    if result.timed_out:
        return Verdict.time_limit
    if result.memory_exceeded:
        return Verdict.memory_limit
    if result.exit_code != 0:
        return Verdict.runtime_error
    if outputs_match(result.stdout, expected_output):
        return Verdict.passed
    return Verdict.wrong_answer


def compute_score(verdicts: Mapping[int, Verdict], weights: Mapping[int, int]) -> int:
    """Percentage (0-100) of the total test weight that passed (decision D14).

    ``verdicts`` maps test case id -> verdict, ``weights`` maps test case id -> weight.
    A test without a verdict counts as failed.
    """
    total = sum(weights.values())
    if total <= 0:
        return 0
    earned = sum(
        weight for test_id, weight in weights.items() if verdicts.get(test_id) == Verdict.passed
    )
    return round(100 * earned / total)


_TRACEBACK_LINE = re.compile(r'File ".*?", line (\d+)')


def extract_error_excerpt(stderr: str, max_length: int = 200) -> str | None:
    """Short form of a Python traceback, for example ``IndexError, line 4``."""
    lines = [line.strip() for line in stderr.strip().splitlines() if line.strip()]
    if not lines:
        return None
    error_name = lines[-1].split(":", 1)[0].strip()
    line_numbers = _TRACEBACK_LINE.findall(stderr)
    excerpt = f"{error_name}, line {line_numbers[-1]}" if line_numbers else error_name
    return excerpt[:max_length]


def count_passed(verdicts: Iterable[Verdict]) -> int:
    return sum(1 for verdict in verdicts if verdict == Verdict.passed)
