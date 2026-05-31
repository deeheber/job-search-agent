FROM public.ecr.aws/docker/library/python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.15 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project --no-editable

COPY README.md ./
COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

ENV LOG_LEVEL=INFO

EXPOSE 8080 8000

CMD ["opentelemetry-instrument", "python", "src/agentcore_app.py"]
