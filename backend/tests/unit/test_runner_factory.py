import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.runner.docker_runner import DockerRunner, _duration_ms
from app.runner.factory import build_runner
from app.runner.subprocess_runner import SubprocessRunner


def test_subprocess_runner_is_refused_outside_dev():
    with pytest.raises(ValidationError, match="only allowed when ENV=dev"):
        Settings(_env_file=None, env="prod", runner="subprocess")


def test_subprocess_runner_is_allowed_in_dev():
    settings = Settings(_env_file=None, env="dev", runner="subprocess")

    assert isinstance(build_runner(settings), SubprocessRunner)


def test_docker_runner_is_the_default_and_takes_its_limits_from_settings():
    settings = Settings(_env_file=None, env="prod", sandbox_pids_limit=32, sandbox_cpus=0.25)

    runner = build_runner(settings)

    assert settings.runner == "docker"
    assert isinstance(runner, DockerRunner)
    assert (runner.pids_limit, runner.cpus) == (32, 0.25)


def test_duration_is_computed_from_docker_timestamps():
    started = "2026-11-12T10:00:00.100000000Z"
    finished = "2026-11-12T10:00:00.350999999Z"

    assert _duration_ms(started, finished) == 250
    assert _duration_ms(started, "0001-01-01T00:00:00Z") == 0
    assert _duration_ms(None, None) == 0
