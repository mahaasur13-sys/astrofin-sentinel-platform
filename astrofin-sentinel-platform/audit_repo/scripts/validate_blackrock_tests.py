# scripts/validate_blackrock_tests.py
# Phase 4 - BlackRock six required tests per agent.

import argparse
import ast
import sys
from pathlib import Path

REQUIRED = [
    "test_happy_path",
    "test_empty_state",
    "test_malformed_state",
    "test_data_source_unavailable",
    "test_missing_ephemeris",
    "test_large_input",
]

AGENTS_DIR = Path("agents/_impl")
TESTS_DIR = Path("tests")


def agent_test_path(agent_file):
    name = agent_file.stem
    return TESTS_DIR / ("test_" + name + ".py")


def has_function(test_file, fn_name):
    try:
        tree = ast.parse(test_file.read_text(encoding="utf-8"))
    except (SyntaxError, FileNotFoundError):
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description="BlackRock six-test validator")
    parser.add_argument("--agents-dir", default=str(AGENTS_DIR))
    parser.add_argument("--tests-dir", default=str(TESTS_DIR))
    args = parser.parse_args()

    agents_dir = Path(args.agents_dir)
    Path(args.tests_dir)

    missing_files = []
    incomplete_files = []

    all_agents = sorted(agents_dir.glob("*.py"))
    for agent_file in all_agents:
        if agent_file.name.startswith("_"):
            continue
        test_file = agent_test_path(agent_file)
        if not test_file.exists():
            missing_files.append(test_file)
            continue
        missing_fns = [fn for fn in REQUIRED if not has_function(test_file, fn)]
        if missing_fns:
            incomplete_files.append((test_file, missing_fns))

    print("BlackRock six-test validator:")
    print("  scanned:    " + str(len(all_agents)) + " agent files")
    print("  missing:    " + str(len(missing_files)) + " test files")
    print("  incomplete: " + str(len(incomplete_files)) + " test files (warn)")

    if missing_files:
        print("--- Missing test files (HARD FAIL) ---")
        print("  agents without tests/test_<agent>.py:")
        for p in missing_files:
            print("    " + str(p))

    if incomplete_files:
        print("--- Incomplete test files (WARN) ---")
        print("  test files missing some of the six required functions:")
        for p, fns in incomplete_files:
            print("    " + str(p) + " -> " + str(fns))

    if missing_files:
        return 1
    if incomplete_files:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
