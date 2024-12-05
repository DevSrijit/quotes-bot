FROM python:3.13-alpine

WORKDIR /home/app

# Install essential build dependencies
RUN apk add --no-cache zlib-dev jpeg-dev gcc musl-dev g++ libffi-dev

RUN python3 -m pip install --upgrade pip

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies with pip
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Kolkata

# Command to run the application
CMD ["python", "src/main.py"]
