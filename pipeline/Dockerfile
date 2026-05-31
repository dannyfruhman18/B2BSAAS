FROM python:3.11-slim

# Install system deps: chromium for Lighthouse, Node.js for npm/lighthouse CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    nodejs \
    npm \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Lighthouse CLI globally
RUN npm install -g lighthouse --unsafe-perm

# Point Lighthouse at the system Chromium
ENV CHROME_PATH=/usr/bin/chromium
ENV LIGHTHOUSE_BIN=lighthouse

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Create data directory for SQLite
RUN mkdir -p /data
ENV DB_PATH=/data/brightwick.db

EXPOSE 8000

CMD ["python", "pipeline_runner.py", "serve"]
