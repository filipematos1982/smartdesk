# Keep the existing Python version and local training workflows.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Retain test dependencies for the current local validation scripts.
COPY requirements.txt requirements.lock ./
# Install the reviewed Python 3.12 resolution rather than resolve version ranges.
RUN pip install --no-cache-dir -r requirements.lock

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

# Readiness checks the database without restarting an otherwise live process.
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=6 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=3).close()"]

# Keep the existing application entry point.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
