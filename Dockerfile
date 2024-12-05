FROM python:3.13-slim

WORKDIR /home/app

# Install dependencies
RUN apt-get update && apt-get install -y \
    zlib1g-dev libjpeg-dev gcc g++ libffi-dev && \
    apt-get clean

RUN python3 -m pip install --upgrade pip

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs

ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Kolkata

CMD ["python", "src/main.py"]