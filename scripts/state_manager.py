#!/usr/bin/env python3
"""
Scheduled job for event state transitions.

Run hourly via cron to automatically transition events based on activity rules.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tradz.events.state_manager import EventStateManager
from src.tradz.database import get_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / "data" / "state_manager.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Run state transitions and store results."""
    parser = argparse.ArgumentParser(description="Run event state transitions")
    parser.add_argument("--reactivation", action="store_true",
                       help="Enable reactivation of resolved/dismissed events")
    parser.add_argument("--log-results", action="store_true",
                       help="Log detailed transition results")
    args = parser.parse_args()

    logger.info(f"Starting state transitions at {datetime.now()}")

    try:
        # Get database connection
        db = get_database()

        # Create state manager
        manager = EventStateManager(db)

        # Run transitions
        results = manager.run_state_transitions()

        # Optionally enable reactivation
        if args.reactivation:
            reactivation_results = manager.check_reactivation_eligibility()
            results.update({
                "resolved_reactivated": reactivation_results["resolved"],
                "dismissed_reactivated": reactivation_results["dismissed"],
            })

        # Store results in run_history
        if results['new_to_ongoing'] > 0 or results['ongoing_to_stale'] > 0:
            store_transition_run(db, results)

        # Log results
        if args.log_results or sum(results.values()) > 0:
            manager.log_state_transitions(results)
            print(f"State transitions completed: {results}")
        else:
            print("No state transitions needed")

        logger.info(f"State transitions completed at {datetime.now()}")
        return 0

    except Exception as e:
        logger.error(f"Error running state transitions: {e}", exc_info=True)
        return 1


def store_transition_run(db, results: dict):
    """Store state transition results in run history."""
    from uuid import uuid4

    run_id = str(uuid4())
    metadata = {
        "type": "state_manager",
        "transitions": results,
    }

    db.start_run(run_id, metadata)
    db.complete_run(
        run_id,
        observations_count=0,
        events_count=sum(results.values()),
        signals_count=0,
    )


if __name__ == "__main__":
    sys.exit(main())
