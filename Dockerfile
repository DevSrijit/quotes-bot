FROM python:3.13-slim

WORKDIR /home/app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

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
