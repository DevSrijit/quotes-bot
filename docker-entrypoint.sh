#!/bin/bash

# Wait for venv to be mounted and available
max_retries=30
counter=0
while [ ! -f "/home/app/venv/bin/python" ] && [ $counter -lt $max_retries ]; do
    echo "Waiting for venv to be mounted... ($counter/$max_retries)"
    sleep 1
    counter=$((counter + 1))
done

if [ ! -f "/home/app/venv/bin/python" ]; then
    echo "Error: Virtual environment not found after $max_retries seconds"
    exit 1
fi

echo "Virtual environment found, starting application..."
exec /home/app/venv/bin/python src/main.py
