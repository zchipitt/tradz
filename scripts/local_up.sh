#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Create logs directory if it doesn't exist
mkdir -p logs

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check for .env
if [ ! -f ".env" ]; then
    echo "Error: .env file not found."
    echo "Please run: cp .env.example .env"
    exit 1
fi

echo "Starting Backend on port 8002..."
source .venv/bin/activate
nohup uvicorn api.main:app --reload --port 8002 > logs/backend.log 2>&1 &
echo "Backend started. Logs in logs/backend.log"

echo "Starting Frontend..."
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
echo "Frontend started. Logs in logs/frontend.log"

echo ""
echo "=================================================="
echo " TRADZ LOCAL ENVIRONMENT IS UP"
echo "=================================================="
echo "Backend API: http://localhost:8002/api/docs"
echo "Frontend:    http://localhost:5173 (check logs if 5173 is busy)"
echo "Logs:        logs/backend.log, logs/frontend.log"
echo "To stop:     ./scripts/local_down.sh"
echo "=================================================="
