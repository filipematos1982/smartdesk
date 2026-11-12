# Keep the existing Python version and local training workflows.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Retain test dependencies for the current local validation scripts.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Use a stable, unprivileged identity and a writable report directory.
RUN groupadd --gid 10001 smartdesk \
    && useradd --uid 10001 --gid 10001 --create-home smartdesk \
    && mkdir -p /app/reports \
    && chown 10001:10001 /app/reports

# Allow only the application and its existing demo and validation inputs.
# Source files remain owned by root and are not writable by the runtime user.
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY tests/ ./tests/
COPY features/ ./features/

USER 10001:10001

EXPOSE 8000

# Keep the existing entry point; no new health endpoint is introduced.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
