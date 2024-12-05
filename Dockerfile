FROM python:3.13-slim

WORKDIR /home/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Kolkata

# Use entrypoint script
ENTRYPOINT ["/home/app/docker-entrypoint.sh"]
CMD []