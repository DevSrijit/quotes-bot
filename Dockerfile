FROM python:3.13

WORKDIR /home/app

# Install only the essential build dependencies
RUN apk add -u zlib-dev jpeg-dev gcc musl-dev

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
