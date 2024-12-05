#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if the process is running
if pm2 list | grep -q "science-quotes-bot"; then
    echo "Service already running, restarting..."
    pm2 restart science-quotes-bot
else
    echo "Starting service..."
    pm2 start ecosystem.config.js
fi

# Save PM2 process list
pm2 save
