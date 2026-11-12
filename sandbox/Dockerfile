# Image in which student code runs. Nothing but Python: no extra packages, no tools.
FROM python:3.12-slim

# An unprivileged user with no home directory and no login shell.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin sandbox \
    && mkdir /sandbox

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /sandbox
USER 10001:10001

# The runner mounts main.py and input.txt read-only into /sandbox.
CMD ["sh", "-c", "python /sandbox/main.py < /sandbox/input.txt"]
