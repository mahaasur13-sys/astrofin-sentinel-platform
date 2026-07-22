#!/usr/bin/env python3
"""
#ACOS #LOAD_TEST
Load Test Runner — entry point for all ACOS load tests
Usage: python3 load_test/run.py [scenario_name|all]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    import os, glob

    if len(sys.argv) > 1 and sys.argv[1] != "all":
        scenario = sys.argv[1]
        print(f"Running single scenario: {scenario}")
        from load_test.orchestrator.__main__ import run_scenario
        r = run_scenario(scenario)
        import json
        print(json.dumps(r, indent=2, default=str))
    else:
        print("Running full orchestrator...")
        from load_test.orchestrator.__main__ import main
        sys.exit(main())
