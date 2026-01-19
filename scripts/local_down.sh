#!/bin/bash

echo "Stopping local environment..."

# Function to kill process on port
kill_port() {
    local port=$1
    local name=$2
    local pid=$(lsof -t -i:$port)
    
    if [ -n "$pid" ]; then
        echo "Stopping $name on port $port (PID $pid)..."
        kill $pid
        echo "$name stopped."
    else
        echo "$name not running on port $port."
    fi
}

# Kill Backend
kill_port 8002 "Backend"

# Kill Frontend (check common Vite ports)
kill_port 5173 "Frontend (5173)"
kill_port 5174 "Frontend (5174)"
kill_port 5175 "Frontend (5175)"

echo "Environment stopped."
