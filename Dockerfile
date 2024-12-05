FROM python:3.11-slim 

WORKDIR /home/app

# Install only the essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies with pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Kolkata
ENV PATH=/root/.local/bin:$PATH

# Command to run the application
CMD ["python", "src/main.py"]
