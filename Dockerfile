
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Update Debian packages to receive security fixes
RUN apt-get update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get install -y --no-install-recommends libgomp1 && \
    rm -rf /var/lib/apt/lists/*



# Install Python dependencies
COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt && \
    python -m pip install --no-cache-dir --upgrade \
    "setuptools>=78.1.1" \
    "wheel>=0.46.2" \
    "jaraco.context>=6.1.0" && \
    python -m pip check && \
    python -c "import importlib.metadata as m; \
    packages = {'setuptools': '78.1.1', \
    'wheel': '0.46.2', \
    'jaraco.context': '6.1.0'}; \
    [print(name, m.version(name)) for name in packages]; \
    assert all(tuple(map(int, m.version(name).split('.')[:3])) >= tuple(map(int, version.split('.'))) for name, version in packages.items())"



# Create non-root application user
RUN groupadd --gid 10001 appgroup && \
    useradd --uid 10001 \
    --gid appgroup \
    --create-home \
    --shell /usr/sbin/nologin \
    appuser

# Copy application source
COPY --chown=appuser:appgroup app.py .
COPY --chown=appuser:appgroup models/ ./models/
COPY --chown=appuser:appgroup templates/ ./templates/
COPY --chown=appuser:appgroup static/ ./static/

# Create writable prediction history directory
RUN mkdir -p /app/prediction_logs && \
    chown -R appuser:appgroup /app/prediction_logs

# Run as non-root user
USER appuser

EXPOSE 5000

# Container health check
HEALTHCHECK --interval=30s \
    --timeout=5s \
    --start-period=60s \
    --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)"

# Production server
CMD ["gunicorn", "--workers", "1", "--threads", "2", "--timeout", "60", "--bind", "0.0.0.0:5000", "app:app"]
