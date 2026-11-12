"""The same functional suite on both runners: ordinary programs must get identical verdicts."""

import pytest

from app.models.submission import Verdict
from app.runner.base import Limits
from app.runner.subprocess_runner import SubprocessRunner
from app.services.scoring import decide_verdict

LIMITS = Limits(time_limit_ms=2000)

DIGIT_SUM = """
n = abs(int(input()))
total = 0
while n > 0:
    total += n % 10
    n //= 10
print(total)
"""

CASES = [
    # (name, code, stdin, expected output, expected verdict)
    ("prints text", 'print("hello")', "", "hello\n", Verdict.passed),
    ("reads stdin", "print(int(input()) * 2)", "21\n", "42\n", Verdict.passed),
    ("digit sum", DIGIT_SUM, "-9075\n", "21\n", Verdict.passed),
    ("several lines", "for i in range(3):\n    print(i)", "", "0\n1\n2\n", Verdict.passed),
    ("trailing spaces are ignored", 'print("10   ")', "", "10\n", Verdict.passed),
    ("unicode output", 'print("ăîșț")', "", "ăîșț\n", Verdict.passed),
    ("wrong answer", "print(41)", "", "42\n", Verdict.wrong_answer),
    ("no output", "pass", "", "42\n", Verdict.wrong_answer),
    ("exception", "raise ValueError('boom')", "", "42\n", Verdict.runtime_error),
    ("syntax error", "def broken(:\n    pass", "", "42\n", Verdict.runtime_error),
    ("non-zero exit", "import sys\nprint(42)\nsys.exit(3)", "", "42\n", Verdict.runtime_error),
    ("missing input", "print(input())", "", "x\n", Verdict.runtime_error),
    ("infinite loop", "while True:\n    pass", "", "42\n", Verdict.time_limit),
]


@pytest.fixture(params=["subprocess", pytest.param("docker", marks=pytest.mark.docker)])
def runner(request):
    if request.param == "subprocess":
        return SubprocessRunner()
    return request.getfixturevalue("docker_runner")


@pytest.mark.parametrize(
    ("code", "stdin", "expected", "verdict"),
    [case[1:] for case in CASES],
    ids=[case[0] for case in CASES],
)
def test_runner_contract(runner, code, stdin, expected, verdict):
    result = runner.run(code, stdin, LIMITS)

    assert decide_verdict(result, expected) == verdict
    assert result.runtime_ms >= 0


def test_stderr_carries_the_traceback(runner):
    result = runner.run("raise ValueError('boom')", "", LIMITS)

    assert "ValueError: boom" in result.stderr
    assert result.stdout == ""
