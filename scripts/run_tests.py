#!/usr/bin/env python3
"""
Test automation script for Phase 3
Runs all test suites and generates coverage report
"""

import sys
import subprocess
import time
import os
from pathlib import Path


def print_status(message):
    """Print status message."""
    print(f"[INFO] {message}")


def print_error(message):
    """Print error message."""
    print(f"[ERROR] {message}", file=sys.stderr)


def print_warning(message):
    """Print warning message."""
    print(f"[WARNING] {message}")


def check_dynamodb_local():
    """Check if DynamoDB Local is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=dynamodb-local", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=False
        )
        if "dynamodb-local" in result.stdout:
            print_status("DynamoDB Local is running")
            return True
        else:
            print_warning("DynamoDB Local is not running")
            return False
    except FileNotFoundError:
        print_warning("Docker not found. E2E tests will be skipped.")
        return False


def start_dynamodb_local():
    """Start DynamoDB Local using docker-compose."""
    try:
        print_status("Starting DynamoDB Local...")
        subprocess.run(
            ["docker-compose", "up", "-d", "dynamodb-local"],
            check=True,
            capture_output=True
        )
        time.sleep(3)  # Wait for DynamoDB to be ready
        if check_dynamodb_local():
            print_status("DynamoDB Local started successfully")
            return True
        else:
            print_error("Failed to start DynamoDB Local")
            return False
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to start DynamoDB Local: {e}")
        return False
    except FileNotFoundError:
        print_warning("docker-compose not found. E2E tests will be skipped.")
        return False


def run_test_suite(suite_name, test_path):
    """Run a test suite."""
    print_status(f"Running {suite_name} tests...")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            ["pytest", test_path, "-v", "--tb=short"],
            check=False
        )
        if result.returncode == 0:
            print_status(f"{suite_name} tests passed")
            return True
        else:
            print_error(f"{suite_name} tests failed")
            return False
    except FileNotFoundError:
        print_error("pytest not found. Please install: pip install pytest")
        return False


def generate_coverage_report():
    """Generate coverage report."""
    print_status("Generating coverage report...")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            [
                "pytest",
                "--cov=src",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-report=term:skip-covered",
                "-q",
                "tests/"
            ],
            check=False,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_status("Coverage report generated")
            print_status("HTML report: htmlcov/index.html")
            
            # Extract coverage percentage
            for line in result.stdout.split('\n'):
                if 'TOTAL' in line and '%' in line:
                    parts = line.split()
                    for part in parts:
                        if part.endswith('%'):
                            coverage = part.rstrip('%')
                            try:
                                coverage_float = float(coverage)
                                if coverage_float >= 80:
                                    print_status(f"Coverage: {coverage}% (meets 80% requirement)")
                                else:
                                    print_warning(f"Coverage: {coverage}% (below 80% requirement)")
                                    return False
                            except ValueError:
                                pass
            return True
        else:
            print_error("Coverage report generation failed")
            return False
    except FileNotFoundError:
        print_error("pytest not found. Please install: pip install pytest pytest-cov")
        return False


def main():
    """Main execution."""
    # Check if we're in the project root
    if not Path("requirements.txt").exists():
        print_error("Must run from project root directory")
        sys.exit(1)
    
    print_status("Starting test automation...")
    print("=" * 50)
    
    # Parse arguments
    unit_only = "--unit-only" in sys.argv
    skip_playwright = "--skip-playwright" in sys.argv
    
    # Check Python version (warn but don't fail for Python 3.9+)
    if sys.version_info < (3, 9):
        print_error("Python 3.9+ required")
        sys.exit(1)
    elif sys.version_info < (3, 11):
        print_warning(f"Python {sys.version_info.major}.{sys.version_info.minor} detected. Python 3.11+ recommended.")
    
    # Install dependencies if needed
    print_status("Checking dependencies...")
    try:
        subprocess.run(
            ["pip", "install", "-q", "-r", "requirements.txt"],
            check=False
        )
    except FileNotFoundError:
        print_warning("pip not found. Please install dependencies manually.")
    
    # Check DynamoDB Local (needed for E2E tests)
    dynamodb_available = False
    if not unit_only:
        if check_dynamodb_local():
            dynamodb_available = True
        else:
            if start_dynamodb_local():
                dynamodb_available = True
    
    # Track test results
    tests_failed = False
    
    # Run unit tests
    print()
    if not run_test_suite("Unit", "tests/unit/"):
        tests_failed = True
    
    # Run integration tests
    print()
    if not run_test_suite("Integration", "tests/integration/"):
        tests_failed = True
    
    # Run E2E tests (if DynamoDB Local is available)
    if not unit_only:
        print()
        if dynamodb_available:
            if not run_test_suite("E2E", "tests/e2e/"):
                tests_failed = True
        else:
            print_warning("Skipping E2E tests (DynamoDB Local not available)")
    
    # Run Playwright MCP tests (optional)
    if not skip_playwright:
        print()
        playwright_tests = Path("tests/playwright")
        if playwright_tests.exists() and any(Path("tests/playwright").glob("test_*.py")):
            if not run_test_suite("Playwright MCP", "tests/playwright/"):
                tests_failed = True
        else:
            print_warning("No Playwright MCP tests found (skipping)")
    
    # Generate coverage report
    print()
    if not generate_coverage_report():
        tests_failed = True
    
    # Final summary
    print()
    print("=" * 50)
    if not tests_failed:
        print_status("All tests passed!")
        print_status("Coverage report: htmlcov/index.html")
        sys.exit(0)
    else:
        print_error("Some tests failed. Check output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

