"""SubprocessRunner with small programs written here (never with student code)."""

from app.runner.base import Limits
from app.runner.subprocess_runner import SubprocessRunner

LIMITS = Limits(time_limit_ms=3000)


def test_prints_text():
    result = SubprocessRunner().run('print("hello")', "", LIMITS)

    assert result.stdout.strip() == "hello"
    assert result.exit_code == 0
    assert result.timed_out is False


def test_reads_stdin():
    result = SubprocessRunner().run("print(int(input()) * 2)", "21\n", LIMITS)

    assert result.stdout.strip() == "42"


def test_exception_gives_non_zero_exit_code_and_stderr():
    result = SubprocessRunner().run("raise ValueError('boom')", "", LIMITS)

    assert result.exit_code != 0
    assert "ValueError: boom" in result.stderr


def test_infinite_loop_times_out():
    result = SubprocessRunner().run("while True:\n    pass", "", Limits(time_limit_ms=500))

    assert result.timed_out is True
    assert result.exit_code is None
    assert result.runtime_ms >= 500


def test_output_is_truncated_to_the_limit():
    result = SubprocessRunner().run(
        'print("x" * 5000)', "", Limits(time_limit_ms=3000, max_output_bytes=100)
    )

    assert len(result.stdout.encode()) <= 100
