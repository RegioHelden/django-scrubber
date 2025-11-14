# -------------------------------------------------
# Managed by modulesync - DO NOT EDIT
# -------------------------------------------------

FROM python:3.12-slim-bookworm

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=x LC_ALL=C.UTF-8 UV_COMPILE_BYTECODE=0

COPY system_dependencies.txt /app/

RUN sys_deps=$(grep -v '^#' system_dependencies.txt | tr '\n' ' '); \
    apt -y update && \
    apt -y --no-install-recommends install pipx $sys_deps && \
    apt clean && \
    find /usr/share/man /usr/share/locale /usr/share/doc -type f -delete && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN grep -q -w 1000 /etc/group || groupadd --gid 1000 app && \
    id -u app >/dev/null 2>&1 || useradd --gid 1000 --uid 1000 -m app && \
    chown app:app /app

USER app

COPY --chown=app requirements* /app/

ENV PATH=/home/app/.local/bin:/home/app/venv/bin:${PATH} DJANGO_SETTINGS_MODULE=example.settings

RUN pipx install --force uv==0.9.9 && uv venv ~/venv && \
    uv pip install --no-cache --upgrade --requirements /app/requirements-test.txt && \
    uv cache clean

EXPOSE 8000
