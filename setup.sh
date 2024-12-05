#!/bin/bash

echo "Setting up Quotable Science Bot..."

# Create logs directory if it doesn't exist
echo "Creating logs directory..."
mkdir -p logs

# Add .dockerignore if it doesn't exist
if [ ! -f ".dockerignore" ]; then
    echo "Creating .dockerignore..."
    echo "__pycache__/" > .dockerignore
    echo "*.pyc" >> .dockerignore
    echo "logs/" >> .dockerignore
fi

# Start the container
echo "Starting Docker container..."
docker compose down
docker rmi quotes-bot-service 2>/dev/null || true
docker compose up --build -d

echo "Setup complete! Container should be running."
echo "Check logs with: docker compose logs -f"
