import pytest

from app.runner.docker_runner import DockerRunner


@pytest.fixture(scope="session")
def docker_runner() -> DockerRunner:
    """A DockerRunner, or a skip when the daemon or the sandbox image is not available."""
    try:
        runner = DockerRunner()
        runner.client.ping()
        runner.client.images.get(runner.image)
    except Exception as exc:  # daemon down, image not built, ...
        pytest.skip(f"Docker sandbox not available: {exc}")
    return runner


@pytest.fixture(autouse=True)
def no_leftover_containers(request):
    """After every Docker test, nothing labelled autograder=1 may still exist."""
    yield
    if request.node.get_closest_marker("docker") and "docker_runner" in request.fixturenames:
        runner = request.getfixturevalue("docker_runner")
        assert runner.leftover_containers() == []
