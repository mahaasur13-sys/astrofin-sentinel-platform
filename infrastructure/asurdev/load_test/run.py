#!/usr/bin/env python3
"""
#ACOS #LOAD_TEST
Load Test Runner — entry point for all ACOS load tests
Usage: python3 load_test/run.py [scenario_name|all]
"""
import logging
import sys
from pathlib import Path

log = logging.getLogger(__name__)


sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1] != "all":
        scenario = sys.argv[1]
        log.info(f"Running single scenario: {scenario}")
        from load_test.orchestrator.__main__ import run_scenario
        r = run_scenario(scenario)
        import json
        log.info(json.dumps(r, indent=2, default=str))
    else:
        log.info("Running full orchestrator...")
        from load_test.orchestrator.__main__ import main
        sys.exit(main())
