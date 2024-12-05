FROM python:3.13-slim

WORKDIR /home/app

# Install system dependencies, including Rust
RUN apt-get update && apt-get install -y --no-install-recommends \
    zlib1g-dev libjpeg-dev gcc g++ libffi-dev curl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    export PATH="/root/.cargo/bin:$PATH" && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN export PATH="/root/.cargo/bin:$PATH" && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Kolkata

# Run the application
CMD ["python", "src/main.py"]