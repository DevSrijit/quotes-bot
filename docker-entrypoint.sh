#!/bin/bash

# Debug: List contents of directories
echo "Checking mount points..."
ls -la /home/app
echo "Checking venv/bin directory..."
ls -la /home/app/venv/bin || echo "venv/bin directory not found"

# Wait for venv to be mounted and available
max_retries=10
counter=0
while [ ! -x "/home/app/venv/bin/python" ] && [ $counter -lt $max_retries ]; do
    echo "Waiting for venv/bin/python to be executable... ($counter/$max_retries)"
    ls -la /home/app/venv/bin/python 2>/dev/null || echo "python not found"
    sleep 1
    counter=$((counter + 1))
done

if [ ! -x "/home/app/venv/bin/python" ]; then
    echo "Error: Python not found or not executable after $max_retries seconds"
    echo "Current directory structure:"
    find /home/app/venv -type f -ls
    exit 1
fi

echo "Virtual environment found!"

# Check if we're in interactive mode
if [ "$1" = "--interactive" ]; then
    echo "Starting interactive shell..."
    exec /bin/bash
else
    echo "Starting application..."
    exec /home/app/venv/bin/python src/main.py
fi
