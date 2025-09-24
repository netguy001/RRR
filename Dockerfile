# Use slim Python base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies (for Pillow, etc. if needed later)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p data static/uploads

# Expose Flask app port (matching your app.py port 5003)
EXPOSE 5003

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5003/ || exit 1

# Run with Gunicorn on port 5003 to match your Flask app
CMD ["gunicorn", "-w", "4", "-k", "gthread", "--threads", "2", "--bind", "0.0.0.0:5003", "--timeout", "120", "app:app"]