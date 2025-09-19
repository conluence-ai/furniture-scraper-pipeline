# Use slim Python image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install minimal system dependencies for Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget ca-certificates libnss3 libatk-bridge2.0-0 libgtk-3-0 \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 \
    libcups2 libpangocairo-1.0-0 libxshmfence1 libpango-1.0-0 \
    libatk1.0-0 libxkbcommon0 libdrm2 libwayland-client0 libwayland-server0 \
    libwayland-egl1 libdbus-1-3 libexpat1 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn gevent

# Install Playwright Chromium only
RUN pip install --no-cache-dir playwright \
    && playwright install chromium \
    && rm -rf /root/.cache/ms-playwright

# Copy backend and frontend
COPY backend ./backend
COPY frontend ./frontend

# Expose port
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl --fail http://localhost:8001/health || exit 1

# Run Gunicorn
CMD ["gunicorn", "-w", "1", "-k", "gevent", "-b", "0.0.0.0:8001", "backend.main:app"]
