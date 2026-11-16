
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system library used by scientific Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgomp1 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app.py .
COPY models/ ./models/
COPY templates/ ./templates/
COPY static/ ./static/

# Create directory for prediction history
RUN mkdir -p /app/prediction_logs

# Application port
EXPOSE 5000

# Container health check
HEALTHCHECK --interval=30s \
    --timeout=5s \
    --start-period=60s \
    --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)"

# Run Flask through Gunicorn
CMD ["gunicorn", "--workers", "1", "--threads", "2", "--timeout", "60", "--bind", "0.0.0.0:5000", "app:app"]
