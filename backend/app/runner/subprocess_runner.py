"""Prototype runner: a plain child process on the host.

THIS IS NOT A SANDBOX. The code runs with the same rights as the server: it can read files,
delete data and use the network. Use it only locally, only with code you wrote yourself.
The memory limit is not enforced here.
"""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from app.runner.base import Limits, RunResult, truncate_output


class SubprocessRunner:
    def run(self, code: str, stdin: str, limits: Limits) -> RunResult:
        with tempfile.TemporaryDirectory(prefix="autograder-") as workdir:
            path = Path(workdir) / "main.py"
            path.write_text(code, encoding="utf-8")
            started = time.perf_counter()
            try:
                completed = subprocess.run(
                    [sys.executable, "-I", str(path)],  # -I: ignore env vars and user site
                    input=stdin,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=limits.time_limit_ms / 1000,
                    cwd=workdir,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                return RunResult(
                    stdout=truncate_output(_text(exc.stdout), limits.max_output_bytes),
                    stderr=truncate_output(_text(exc.stderr), limits.max_output_bytes),
                    exit_code=None,
                    runtime_ms=_elapsed_ms(started),
                    timed_out=True,
                )
            return RunResult(
                stdout=truncate_output(completed.stdout, limits.max_output_bytes),
                stderr=truncate_output(completed.stderr, limits.max_output_bytes),
                exit_code=completed.returncode,
                runtime_ms=_elapsed_ms(started),
            )


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
