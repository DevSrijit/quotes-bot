FROM python:3.13-slim

WORKDIR /home/app

# Only install runtime dependencies, no build tools needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from host
COPY venv venv/

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Kolkata
ENV PATH="/home/app/venv/bin:$PATH"
ENV PYTHONPATH="/home/app/venv/lib/python3.13/site-packages:$PYTHONPATH"

# Run the application
CMD ["python", "src/main.py"]