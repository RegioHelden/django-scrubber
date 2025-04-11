FROM python:3.12-slim-bookworm

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=x LC_ALL=C.UTF-8 UV_COMPILE_BYTECODE=0

RUN apt-get -y update && apt-get -y install \
        build-essential \
        gcc \
        python3-venv \
        python3-dev \
        libffi-dev \
        libssl-dev \
        pipx \
    && \
    apt-get clean

WORKDIR /app

RUN grep -q -w 1000 /etc/group || groupadd --gid 1000 app && \
    id -u app >/dev/null 2>&1 || useradd --gid 1000 --uid 1000 -m app && \
    chown app:app /app

USER app

COPY --chown=app requirements* /app/

ENV PATH=/home/app/.local/bin:/home/app/venv/bin:${PATH} DJANGO_SETTINGS_MODULE=tests.settings

RUN pipx install --force uv==0.6.14 && uv venv ~/venv && \
    uv pip install --no-cache --upgrade --requirements /app/requirements-test.txt && \
    uv cache clean

EXPOSE 8000
