#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "Virtual environment already exists"
fi

# Create logs directory
mkdir -p logs

# Start the container
docker compose up --build -d

echo "Setup complete! Container should be running."
echo "Check logs with: docker compose logs -f"
