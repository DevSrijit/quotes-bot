FROM python:3.13-slim

WORKDIR /home/app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Kolkata
ENV PYTHONPATH="/home/app/venv/lib/python3.13/site-packages:$PYTHONPATH"

# Use entrypoint script
ENTRYPOINT ["/home/app/docker-entrypoint.sh"]
# Default to non-interactive mode
CMD []