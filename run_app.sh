#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the FastAPI application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
