#!/bin/bash
# Event State Transition Script
# Runs hourly state transitions for the event system
#
# Cron setup (hourly at minute 0):
#   0 * * * * /path/to/tradz/scripts/state_transitions.sh >> /path/to/tradz/logs/state_transitions.log 2>&1

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "Event State Transitions"
echo "============================================================"
echo "Time: $(date)"
echo "============================================================"

# Change to project root
cd "$PROJECT_ROOT"

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found at .venv"
    exit 1
fi

# Activate virtual environment and run script
source .venv/bin/activate
python3 scripts/run_state_transitions.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ State transitions completed successfully"
else
    echo "❌ State transitions failed"
    exit 1
fi
