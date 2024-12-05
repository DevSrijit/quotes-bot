#!/bin/bash

echo "Setting up Quotable Science Bot..."

# Clean up any existing venv
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create fresh virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Verify python exists in venv
if [ ! -f "venv/bin/python" ]; then
    echo "Error: Python not found in virtual environment"
    ls -la venv/bin/
    exit 1
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Verify dependencies are installed
echo "Verifying installation..."
venv/bin/pip list

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

# Set correct permissions for venv
echo "Setting permissions..."
chmod -R 755 venv/
chmod 644 venv/pyvenv.cfg

# Start the container
echo "Starting Docker container..."
docker compose down
docker rmi quotes-bot-service 2>/dev/null || true
docker compose up --build -d

echo "Setup complete! Container should be running."
echo "Check logs with: docker compose logs -f"
