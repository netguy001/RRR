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

# Create necessary directories and set permissions
RUN mkdir -p data static/uploads && \
    chmod 755 data static/uploads

# Create an initialization script
RUN echo '#!/bin/bash\n\
    echo "Initializing application..."\n\
    python3 -c "\n\
    import os\n\
    import json\n\
    from werkzeug.security import generate_password_hash\n\
    \n\
    # Ensure directories exist\n\
    os.makedirs(\"data\", exist_ok=True)\n\
    os.makedirs(\"static/uploads\", exist_ok=True)\n\
    \n\
    # Initialize files if they dont exist\n\
    files_to_init = [\"data/projects.json\", \"data/messages.json\", \"data/testimonials.json\"]\n\
    for file_path in files_to_init:\n\
    if not os.path.exists(file_path):\n\
    with open(file_path, \"w\") as f:\n\
    json.dump([], f, indent=4)\n\
    print(f\"Created {file_path}\")\n\
    \n\
    # Initialize admin file if it doesnt exist\n\
    admin_file = \"data/admin.json\"\n\
    if not os.path.exists(admin_file):\n\
    admin_data = {\n\
    \"username\": \"admin\",\n\
    \"password\": generate_password_hash(\"rrr_admin_2025!\"),\n\
    \"email\": \"admin@rrrconstruction.com\"\n\
    }\n\
    with open(admin_file, \"w\") as f:\n\
    json.dump(admin_data, f, indent=4)\n\
    print(f\"Created {admin_file}\")\n\
    else:\n\
    print(f\"{admin_file} already exists\")\n\
    "\n\
    echo "Initialization complete!"\n\
    exec "$@"' > /app/init.sh && chmod +x /app/init.sh

# Expose Flask app port (matching your app.py port 5003)
EXPOSE 5003

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5003/ || exit 1

# Use the initialization script as entrypoint
ENTRYPOINT ["/app/init.sh"]

# Run with Gunicorn on port 5003 to match your Flask app
CMD ["gunicorn", "-w", "4", "-k", "gthread", "--threads", "2", "--bind", "0.0.0.0:5003", "--timeout", "120", "app:app"]