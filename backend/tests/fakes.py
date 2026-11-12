"""Test doubles."""

from collections.abc import Callable

from app.runner.base import Limits, RunResult


def ok(stdout: str, runtime_ms: int = 30) -> RunResult:
    return RunResult(stdout=stdout, stderr="", exit_code=0, runtime_ms=runtime_ms)


def crash(stderr: str = "Traceback...\nValueError: boom") -> RunResult:
    return RunResult(stdout="", stderr=stderr, exit_code=1, runtime_ms=25)


def timeout() -> RunResult:
    return RunResult(stdout="", stderr="", exit_code=None, runtime_ms=2000, timed_out=True)


def out_of_memory() -> RunResult:
    return RunResult(stdout="", stderr="", exit_code=137, runtime_ms=80, memory_exceeded=True)


class FakeRunner:
    """Deterministic runner: answers from a script instead of executing anything.

    ``script`` is either a list of results (returned in call order) or a function
    ``(code, stdin, limits) -> RunResult``. Items that are exceptions are raised.
    """

    def __init__(self, script: list[RunResult | Exception] | Callable[..., RunResult]):
        self.script = script
        self.calls: list[tuple[str, str, Limits]] = []

    def run(self, code: str, stdin: str, limits: Limits) -> RunResult:
        self.calls.append((code, stdin, limits))
        if callable(self.script):
            return self.script(code, stdin, limits)
        item = self.script[len(self.calls) - 1]
        if isinstance(item, Exception):
            raise item
        return item


def echo_runner() -> FakeRunner:
    """Pretends the program prints the digit sum of its input, ignoring the sign."""

    def run(code: str, stdin: str, limits: Limits) -> RunResult:
        digits = [int(char) for char in stdin if char.isdigit()]
        return ok(f"{sum(digits)}\n")

    return FakeRunner(run)
