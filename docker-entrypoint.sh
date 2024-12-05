#!/bin/bash

# Debug: List contents of directories
echo "Checking mount points..."
ls -la /home/app
echo "Checking venv directory..."
ls -la /home/app/venv || echo "venv directory not found"

# Wait for venv to be mounted and available
max_retries=10
counter=0
while [ ! -f "/home/app/venv/bin/python" ] && [ $counter -lt $max_retries ]; do
    echo "Waiting for venv to be mounted... ($counter/$max_retries)"
    ls -la /home/app/venv || echo "venv directory not found"
    sleep 1
    counter=$((counter + 1))
done

if [ ! -f "/home/app/venv/bin/python" ]; then
    echo "Error: Virtual environment not found after $max_retries seconds"
    echo "Current directory structure:"
    find /home/app -maxdepth 3 -ls
    exit 1
fi

echo "Virtual environment found, starting application..."
exec /home/app/venv/bin/python src/main.py
