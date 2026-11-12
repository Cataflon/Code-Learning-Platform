"""Sandbox runner: one throw-away container per test, with strict limits.

Each option below blocks a specific attack:

* network_disabled        no network access (no data exfiltration, no downloads)
* mem_limit = memswap     the host's memory cannot be exhausted, and swap cannot be used instead
* nano_cpus               a busy loop cannot take every core
* pids_limit              fork bombs stop at a small number of processes
* read_only + tmpfs /tmp  nothing can be written except a small in-memory /tmp
* cap_drop ALL            no Linux capabilities at all
* no-new-privileges       setuid binaries cannot raise privileges
* user                    an unprivileged uid, so a container escape lands as nobody
* bind mount, read-only   the code and the input cannot be modified from inside

The limits are enforced by Docker (cgroups and namespaces), never by the student's code.
"""

import contextlib
import os
import tempfile
from datetime import datetime
from pathlib import Path

import docker
import requests
from docker.errors import DockerException, NotFound
from docker.types import LogConfig

from app.runner.base import Limits, RunResult, truncate_output

LABEL = {"autograder": "1"}
SIGKILL_EXIT_CODE = 137  # 128 + signal 9
COMMAND = ["sh", "-c", "exec python /sandbox/main.py < /sandbox/input.txt"]


class DockerRunner:
    def __init__(
        self,
        image: str = "autograder-python:latest",
        cpus: float = 0.5,
        pids_limit: int = 64,
        startup_margin_ms: int = 2000,
        client: docker.DockerClient | None = None,
    ) -> None:
        self.image = image
        self.cpus = cpus
        self.pids_limit = pids_limit
        # Wall-clock allowance for creating and starting the container, on top of the limit.
        self.startup_margin_ms = startup_margin_ms
        self._client = client

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def run(self, code: str, stdin: str, limits: Limits) -> RunResult:
        with tempfile.TemporaryDirectory(prefix="autograder-") as workdir:
            self._write_files(Path(workdir), code, stdin)
            container = self.client.containers.create(
                self.image,
                command=COMMAND,
                network_disabled=True,
                mem_limit=f"{limits.memory_limit_mb}m",
                memswap_limit=f"{limits.memory_limit_mb}m",
                nano_cpus=int(self.cpus * 1_000_000_000),
                pids_limit=self.pids_limit,
                read_only=True,
                tmpfs={"/tmp": "size=16m,noexec"},
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"],
                user="10001:10001",
                working_dir="/sandbox",
                volumes={workdir: {"bind": "/sandbox", "mode": "ro"}},
                labels=LABEL,
                # A program that prints forever must not fill the host's disk.
                log_config=LogConfig(
                    type=LogConfig.types.JSON, config={"max-size": "1m", "max-file": "1"}
                ),
            )
            try:
                return self._run_container(container, limits)
            finally:
                # Always remove the container, whatever happened above.
                with contextlib.suppress(NotFound):
                    container.remove(force=True)

    @staticmethod
    def _write_files(workdir: Path, code: str, stdin: str) -> None:
        (workdir / "main.py").write_text(code, encoding="utf-8", newline="\n")
        (workdir / "input.txt").write_text(stdin, encoding="utf-8", newline="\n")
        # The container user is not the host user: make the files world-readable (Linux hosts).
        os.chmod(workdir, 0o755)
        for name in ("main.py", "input.txt"):
            os.chmod(workdir / name, 0o644)

    def _run_container(self, container, limits: Limits) -> RunResult:
        timeout_s = (limits.time_limit_ms + self.startup_margin_ms) / 1000
        container.start()
        timed_out = False
        exit_code: int | None = None
        try:
            exit_code = container.wait(timeout=timeout_s)["StatusCode"]
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            timed_out = True
            # It may have finished between the timeout and the kill.
            with contextlib.suppress(DockerException):
                container.kill()

        container.reload()
        state = container.attrs["State"]
        runtime_ms = _duration_ms(state.get("StartedAt"), state.get("FinishedAt"))
        if not timed_out and runtime_ms > limits.time_limit_ms:
            # It finished inside the startup margin but ran longer than the limit allows.
            timed_out = True
        memory_exceeded = is_memory_kill(state, exit_code, timed_out)

        stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
        stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
        return RunResult(
            stdout=truncate_output(stdout, limits.max_output_bytes),
            stderr=truncate_output(stderr, limits.max_output_bytes),
            exit_code=None if timed_out else exit_code,
            runtime_ms=min(runtime_ms, limits.time_limit_ms) if timed_out else runtime_ms,
            timed_out=timed_out,
            memory_exceeded=memory_exceeded,
        )

    def leftover_containers(self) -> list:
        """Containers created by this runner that still exist (should always be empty)."""
        return self.client.containers.list(all=True, filters={"label": "autograder=1"})


def is_memory_kill(state: dict, exit_code: int | None, timed_out: bool) -> bool:
    """Was the program stopped by the kernel for exceeding its memory limit?

    Docker's ``OOMKilled`` flag is the direct signal, but it is reported asynchronously and
    is sometimes still false right after the container exits (seen on Linux with cgroup v2).
    Exit code 137 means "killed by SIGKILL". When we did not send that signal ourselves
    (no timeout), the only sender left is the kernel's OOM killer: the program is PID 1 in
    its own namespace, so it cannot SIGKILL itself, and nothing else can reach it.
    """
    if timed_out:
        return False  # 137 here comes from our own kill()
    return bool(state.get("OOMKilled")) or exit_code == SIGKILL_EXIT_CODE


def _parse_docker_time(value: str | None) -> datetime | None:
    """Docker timestamps have nanoseconds; Python parses at most microseconds."""
    if not value or value.startswith("0001-"):
        return None
    head, _, fraction = value.rstrip("Z").partition(".")
    return datetime.fromisoformat(f"{head}.{(fraction + '000000')[:6]}+00:00")


def _duration_ms(started: str | None, finished: str | None) -> int:
    start, end = _parse_docker_time(started), _parse_docker_time(finished)
    if start is None or end is None:
        return 0
    return max(0, int((end - start).total_seconds() * 1000))
