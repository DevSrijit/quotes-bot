#!/bin/bash

# Check if we're in interactive mode
if [ "$1" = "--interactive" ]; then
    echo "Starting interactive shell..."
    exec /bin/bash
else
    echo "Starting application..."
    exec python src/main.py
fi
