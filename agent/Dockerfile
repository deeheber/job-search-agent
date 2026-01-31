FROM public.ecr.aws/docker/library/python:3.13-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir . && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser src/ .

USER appuser

ENV LOG_LEVEL=INFO

EXPOSE 8080 8000

CMD ["opentelemetry-instrument", "python", "agentcore_app.py"]
