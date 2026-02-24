#!/usr/bin/env python3
"""
Test Runner for IntervyoAI
Runs tests in Pyramid Testing pattern: 70% Unit, 20% Integration, 10% Smoke
"""

import sys
import subprocess
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def run_tests(test_type="all", verbose=True):
    """Run tests based on type"""

    test_dir = Path(__file__).parent / "tests"

    cmd = ["pytest", "-v", "--tb=short"]

    if test_type == "unit":
        cmd.append(str(test_dir / "unit"))
        print(f"{BLUE}Running Unit Tests (70%)...{RESET}")
    elif test_type == "integration":
        cmd.append(str(test_dir / "integration"))
        print(f"{BLUE}Running Integration Tests (20%)...{RESET}")
    elif test_type == "smoke":
        cmd.append(str(test_dir / "smoke"))
        print(f"{BLUE}Running Smoke Tests (10%)...{RESET}")
    else:
        cmd.append(str(test_dir))
        print(f"{BLUE}Running All Tests...{RESET}")

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode == 0
    except Exception as e:
        print(f"{RED}Error running tests: {e}{RESET}")
        return False


def main():
    """Main test runner"""
    print(f"{YELLOW}{'=' * 50}{RESET}")
    print(f"{YELLOW}IntervyoAI Test Suite{RESET}")
    print(f"{YELLOW}Pyramid Testing: 70% Unit, 20% Integration, 10% Smoke{RESET}")
    print(f"{YELLOW}{'=' * 50}{RESET}\n")

    # Run all tests
    print(f"\n{BLUE}[1/4] Running Unit Tests (70%)...{RESET}")
    unit_passed = run_tests("unit")

    print(f"\n{BLUE}[2/4] Running Integration Tests (20%)...{RESET}")
    integration_passed = run_tests("integration")

    print(f"\n{BLUE}[3/4] Running Smoke Tests (10%)...{RESET}")
    smoke_passed = run_tests("smoke")

    # Summary
    print(f"\n{YELLOW}{'=' * 50}{RESET}")
    print(f"{YELLOW}Test Summary:{RESET}")

    if unit_passed:
        print(f"  {GREEN}✓ Unit Tests Passed{RESET}")
    else:
        print(f"  {RED}✗ Unit Tests Failed{RESET}")

    if integration_passed:
        print(f"  {GREEN}✓ Integration Tests Passed{RESET}")
    else:
        print(f"  {RED}✗ Integration Tests Failed{RESET}")

    if smoke_passed:
        print(f"  {GREEN}✓ Smoke Tests Passed{RESET}")
    else:
        print(f"  {RED}✗ Smoke Tests Failed{RESET}")

    print(f"{YELLOW}{'=' * 50}{RESET}")

    all_passed = unit_passed and integration_passed and smoke_passed

    if all_passed:
        print(f"{GREEN}All tests passed!{RESET}")
        return 0
    else:
        print(f"{RED}Some tests failed!{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
