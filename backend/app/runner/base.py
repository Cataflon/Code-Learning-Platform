"""The Runner interface: run one program with one input under limits.

The evaluation service depends only on this shape, never on a concrete runner, so the
prototype (SubprocessRunner), the sandbox (DockerRunner) and the test double (FakeRunner)
are interchangeable.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Limits:
    time_limit_ms: int = 2000
    memory_limit_mb: int = 128
    max_output_bytes: int = 64 * 1024


@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int | None
    runtime_ms: int
    timed_out: bool = False
    memory_exceeded: bool = False


class Runner(Protocol):
    def run(self, code: str, stdin: str, limits: Limits) -> RunResult: ...


def truncate_output(text: str, max_bytes: int) -> str:
    """Cut text to at most max_bytes of UTF-8 without splitting a character."""
    data = text.encode("utf-8", errors="replace")
    if len(data) <= max_bytes:
        return text
    return data[:max_bytes].decode("utf-8", errors="ignore")
