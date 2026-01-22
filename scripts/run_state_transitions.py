#!/usr/bin/env python3
"""
Event State Transition Runner

Runs state transitions for the event system.
Can be executed standalone or scheduled via cron for hourly runs.

Usage:
    python scripts/run_state_transitions.py

Cron setup (hourly at minute 0):
    0 * * * * cd /path/to/tradz && .venv/bin/python scripts/run_state_transitions.py >> logs/state_transitions.log 2>&1
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tradz.database import get_database
from src.tradz.events import EventStateManager, run_state_transitions


def main():
    """Run event state transitions."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Event State Transition Runner")
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    try:
        # Get database connection
        db = get_database()

        # Run state transitions
        manager = EventStateManager(db)
        results = manager.run_state_transitions()

        # Log results
        logger.info("State transition results:")
        logger.info(f"  New → Ongoing: {results['new_to_ongoing']}")
        logger.info(f"  Ongoing/New → Stale: {results['ongoing_to_stale']}")
        logger.info(f"  Resolved reactivated: {results['resolved_reactivated']}")
        logger.info(f"  Dismissed reactivated: {results['dismissed_reactivated']}")

        total = sum(results.values())
        logger.info(f"Total transitions: {total}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Error running state transitions: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
