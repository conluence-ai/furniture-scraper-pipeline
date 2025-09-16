# Use a slim Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (curl for healthcheck, build tools for pip if needed)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn gevent

# Copy backend and frontend
COPY backend ./backend
COPY frontend ./frontend

# Expose the Flask/Gunicorn port
EXPOSE 8001

# Add a healthcheck hitting the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl --fail http://localhost:8001/health || exit 1

# Run Gunicorn in production mode
# -w: number of workers (4 is good starting point)
# -k: worker class (sync is fine unless streaming)
# -b: bind to 0.0.0.0:8001
# backend.main:app -> module:application
CMD ["gunicorn", "-w", "1", "-k", "gevent", "-b", "0.0.0.0:8001", "backend.main:app"]
