#!/usr/bin/env python
"""
Test Suite Runner and Summary Generator

This script provides easy commands to run different test configurations
and generates a summary of the test coverage.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}")
    result = subprocess.run(cmd, shell=True, cwd=Path(__file__).parent)
    return result.returncode

def main():
    """Main runner function."""
    if len(sys.argv) < 2:
        print("""
Usage: python run_tests.py <command>

Commands:
  all              - Run all tests (unit + selenium)
  unit             - Run unit tests only
  selenium         - Run selenium tests only
  quick            - Run unit tests quickly (no coverage)
  coverage         - Run all tests with coverage report
  auth             - Run auth tests only
  friends          - Run friends tests only
  events           - Run events tests only
  integration      - Run integration tests only
  verbose          - Run all tests with verbose output
  watch            - Watch for file changes and run tests (requires pytest-watch)

Examples:
  python run_tests.py unit
  python run_tests.py coverage
  python run_tests.py auth
        """)
        return 1

    cmd = sys.argv[1]
    
    commands = {
        'all': ('pytest test/', 'All Tests (Unit + Selenium)'),
        'unit': ('pytest test/ --ignore=test/test_selenium.py', 'Unit Tests Only'),
        'selenium': ('pytest test/test_selenium.py -v', 'Selenium Tests (Live Server)'),
        'quick': ('pytest test/ --ignore=test/test_selenium.py -q', 'Quick Unit Tests'),
        'coverage': ('pytest test/ --cov=. --cov-report=html test/', 'Tests with Coverage Report'),
        'auth': ('pytest test/test_auth.py -v', 'Authentication Tests'),
        'friends': ('pytest test/test_friends.py -v', 'Friends Tests'),
        'events': ('pytest test/test_events.py -v', 'Events Tests'),
        'integration': ('pytest test/test_integration.py -v', 'Integration Tests'),
        'verbose': ('pytest test/ -v', 'All Tests (Verbose)'),
        'watch': ('ptw test/', 'Watch Mode (requires pytest-watch)'),
    }
    
    if cmd not in commands:
        print(f"Unknown command: {cmd}")
        return 1
    
    cmd_str, description = commands[cmd]
    return run_command(cmd_str, description)

if __name__ == '__main__':
    sys.exit(main())
