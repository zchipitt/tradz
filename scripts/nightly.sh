#!/bin/bash
# Nightly trading signal generation script
# Runs the Python script to generate and send daily reports

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "Trading Signals - Nightly Run"
echo "============================================================"
echo "Project root: $PROJECT_ROOT"
echo "Time: $(date)"
echo "============================================================"

# Change to project root
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found at .venv"
    echo "Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Copy .env.example to .env and configure your settings"
    echo "Continuing anyway (will use dry-run mode)..."
fi

# Run the main script
echo "Running signal generation..."
python3 src/tradz/run_nightly.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "============================================================"
    echo "✅ Nightly run completed successfully"
    echo "============================================================"
else
    echo "============================================================"
    echo "❌ Nightly run failed"
    echo "============================================================"
    exit 1
fi
