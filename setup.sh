#!/bin/bash

echo "Setting up Quotable Science Bot..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Add .dockerignore if it doesn't exist
if [ ! -f ".dockerignore" ]; then
    echo "Creating .dockerignore..."
    echo "venv/" > .dockerignore
    echo "logs/" >> .dockerignore
    echo "__pycache__/" >> .dockerignore
    echo "*.pyc" >> .dockerignore
fi

# Start the container
echo "Starting Docker container..."
docker compose up --build -d

echo "Setup complete! Container should be running."
echo "Check logs with: docker compose logs -f"
