#!/bin/bash

# Start script for RAG Automation Project

echo "Starting RAG Automation Project..."

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
    cd /app/backend
    uvicorn main:app --host 0.0.0.0 --port 8000
else
    echo "Running locally"
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt
    
    # Run the application
    echo "Starting server..."
    python main.py
fi
