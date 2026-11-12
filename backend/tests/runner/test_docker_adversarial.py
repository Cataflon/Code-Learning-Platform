"""Hostile programs against the sandbox. Each test names the attack and the option that stops it."""

import time

import pytest

from app.models.submission import Verdict
from app.runner.base import Limits
from app.services.scoring import decide_verdict

pytestmark = pytest.mark.docker

LIMITS = Limits(time_limit_ms=2000, memory_limit_mb=64)


def test_infinite_loop_is_killed_within_the_limit_plus_margin(docker_runner):
    started = time.perf_counter()

    result = docker_runner.run("while True:\n    pass", "", Limits(time_limit_ms=1000))

    elapsed_ms = (time.perf_counter() - started) * 1000
    assert result.timed_out is True
    assert decide_verdict(result, "") == Verdict.time_limit
    # limit + startup margin + a generous allowance for Docker API calls and cleanup
    assert elapsed_ms < 1000 + docker_runner.startup_margin_ms + 5000


def test_sleeping_forever_is_killed_too(docker_runner):
    result = docker_runner.run("import time\ntime.sleep(60)", "", Limits(time_limit_ms=1000))

    assert result.timed_out is True


def test_huge_allocation_gives_memory_limit(docker_runner):
    code = "data = 'x' * (1024 * 1024 * 1024)\nprint(len(data))"

    result = docker_runner.run(code, "", LIMITS)

    assert result.memory_exceeded is True
    assert decide_verdict(result, "") == Verdict.memory_limit


def test_growing_list_gives_memory_limit(docker_runner):
    code = "chunks = []\nwhile True:\n    chunks.append('x' * 10_000_000)"

    result = docker_runner.run(code, "", LIMITS)

    assert decide_verdict(result, "") == Verdict.memory_limit


def test_fork_bomb_is_contained_by_pids_limit(docker_runner):
    code = """
import os, time
children = 0
try:
    while True:
        if os.fork() == 0:
            time.sleep(30)
            os._exit(0)
        children += 1
except OSError:
    print("fork refused after", children)
"""
    result = docker_runner.run(code, "", LIMITS)

    assert "fork refused after" in result.stdout
    refused_after = int(result.stdout.split()[-1])
    assert refused_after < docker_runner.pids_limit


def test_network_is_unreachable(docker_runner):
    code = """
import socket
try:
    socket.create_connection(("1.1.1.1", 80), timeout=1)
    print("connected")
except OSError as exc:
    print("blocked")
"""
    result = docker_runner.run(code, "", LIMITS)

    assert result.stdout.strip() == "blocked"


def test_dns_does_not_resolve(docker_runner):
    code = """
import socket
try:
    socket.gethostbyname("example.com")
    print("resolved")
except OSError:
    print("blocked")
"""
    result = docker_runner.run(code, "", LIMITS)

    assert result.stdout.strip() == "blocked"


@pytest.mark.parametrize("path", ["/sandbox/evil.txt", "/evil.txt", "/etc/evil", "/home/evil"])
def test_writing_outside_tmp_fails(docker_runner, path):
    code = f"""
try:
    open({path!r}, "w").write("x")
    print("written")
except OSError:
    print("blocked")
"""
    result = docker_runner.run(code, "", LIMITS)

    assert result.stdout.strip() == "blocked"


def test_tmp_is_writable_but_small(docker_runner):
    code = """
open("/tmp/ok.txt", "w").write("fine")
print(open("/tmp/ok.txt").read())
try:
    with open("/tmp/big.bin", "wb") as handle:
        for _ in range(64):
            handle.write(b"x" * 1024 * 1024)
    print("wrote 64 MB")
except OSError:
    print("tmp full")
"""
    result = docker_runner.run(code, "", Limits(time_limit_ms=4000, memory_limit_mb=128))

    assert result.stdout.split("\n")[:2] == ["fine", "tmp full"]


def test_the_submitted_code_cannot_be_modified(docker_runner):
    code = """
try:
    open("/sandbox/main.py", "a").write("# changed")
    print("modified")
except OSError:
    print("blocked")
"""
    result = docker_runner.run(code, "", LIMITS)

    assert result.stdout.strip() == "blocked"


def test_huge_output_is_truncated(docker_runner):
    code = "while True:\n    print('x' * 1000)"
    limits = Limits(time_limit_ms=1000, max_output_bytes=64 * 1024)

    result = docker_runner.run(code, "", limits)

    assert len(result.stdout.encode()) <= 64 * 1024
    assert result.timed_out is True


def test_runs_as_unprivileged_user_without_capabilities(docker_runner):
    code = """
import os
print(os.getuid())
status = open("/proc/self/status").read()
print([line.split()[1] for line in status.splitlines() if line.startswith("CapEff")][0])
"""
    result = docker_runner.run(code, "", LIMITS)

    uid, effective_caps = result.stdout.split()
    assert uid == "10001"
    assert int(effective_caps, 16) == 0


def test_no_containers_are_left_behind(docker_runner):
    for code in ("print(1)", "raise SystemExit(2)", "while True:\n    pass"):
        docker_runner.run(code, "", Limits(time_limit_ms=500))

    assert docker_runner.leftover_containers() == []


def test_leftover_containers_from_a_killed_server_are_removed(docker_runner):
    orphan = docker_runner.client.containers.create(
        docker_runner.image, command=["true"], labels={"autograder": "1"}
    )

    removed = docker_runner.remove_leftover_containers()

    assert removed >= 1
    assert orphan.id not in [container.id for container in docker_runner.leftover_containers()]
