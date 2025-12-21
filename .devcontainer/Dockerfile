ARG PYTHON_VERSION=3.12
FROM mcr.microsoft.com/devcontainers/python:${PYTHON_VERSION}

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspaces/value-at-risk

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    git \
    && apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN chown -R vscode:vscode /workspaces/value-at-risk

USER vscode

COPY --chown=vscode:vscode pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev

COPY --chown=vscode:vscode . .
RUN uv sync --frozen
