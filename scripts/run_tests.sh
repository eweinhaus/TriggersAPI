#!/bin/bash

# Test automation script for Phase 3
# Runs all test suites: unit, integration, e2e, playwright
# Generates coverage report
# Exits with proper status code

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if we're in the project root
if [ ! -f "requirements.txt" ]; then
    print_error "Must run from project root directory"
    exit 1
fi

# Check if DynamoDB Local is running
check_dynamodb_local() {
    if docker ps | grep -q dynamodb-local; then
        print_status "DynamoDB Local is running"
        return 0
    else
        print_warning "DynamoDB Local is not running"
        print_status "Starting DynamoDB Local..."
        docker-compose up -d dynamodb-local
        sleep 3  # Wait for DynamoDB to be ready
        if docker ps | grep -q dynamodb-local; then
            print_status "DynamoDB Local started successfully"
            return 0
        else
            print_error "Failed to start DynamoDB Local"
            return 1
        fi
    fi
}

# Run test suite
run_test_suite() {
    local suite_name=$1
    local test_path=$2
    
    print_status "Running $suite_name tests..."
    
    if pytest "$test_path" -v --tb=short; then
        print_status "$suite_name tests passed"
        return 0
    else
        print_error "$suite_name tests failed"
        return 1
    fi
}

# Main execution
print_status "Starting test automation..."
print_status "=================================="

# Check Python and dependencies
if ! command -v python3 &> /dev/null; then
    print_error "python3 not found. Please install Python 3.11+"
    exit 1
fi

# Install/upgrade dependencies if needed
print_status "Checking dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
fi

# Check DynamoDB Local (needed for E2E tests)
DYNAMODB_NEEDED=false
if [ "$1" != "--unit-only" ]; then
    DYNAMODB_NEEDED=true
fi

if [ "$DYNAMODB_NEEDED" = true ]; then
    if ! check_dynamodb_local; then
        print_warning "DynamoDB Local not available. E2E tests will be skipped."
        print_warning "Run: docker-compose up -d dynamodb-local"
    fi
fi

# Track test results
TESTS_FAILED=0

# Run unit tests
print_status ""
print_status "=================================="
print_status "Running Unit Tests"
print_status "=================================="
if ! run_test_suite "Unit" "tests/unit/"; then
    TESTS_FAILED=1
fi

# Run integration tests
print_status ""
print_status "=================================="
print_status "Running Integration Tests"
print_status "=================================="
if ! run_test_suite "Integration" "tests/integration/"; then
    TESTS_FAILED=1
fi

# Run E2E tests (if DynamoDB Local is available)
if [ "$DYNAMODB_NEEDED" = true ] && docker ps | grep -q dynamodb-local; then
    print_status ""
    print_status "=================================="
    print_status "Running E2E Tests"
    print_status "=================================="
    if ! run_test_suite "E2E" "tests/e2e/"; then
        TESTS_FAILED=1
    fi
else
    print_warning "Skipping E2E tests (DynamoDB Local not available)"
fi

# Run Playwright MCP tests (optional, may require MCP server)
if [ "$1" != "--skip-playwright" ]; then
    print_status ""
    print_status "=================================="
    print_status "Running Playwright MCP Tests"
    print_status "=================================="
    if [ -d "tests/playwright" ] && [ "$(ls -A tests/playwright/*.py 2>/dev/null)" ]; then
        if ! run_test_suite "Playwright MCP" "tests/playwright/"; then
            TESTS_FAILED=1
        fi
    else
        print_warning "No Playwright MCP tests found (skipping)"
    fi
fi

# Generate coverage report
print_status ""
print_status "=================================="
print_status "Generating Coverage Report"
print_status "=================================="
if pytest --cov=src --cov-report=html --cov-report=term-missing --cov-report=term:skip-covered -q tests/; then
    print_status "Coverage report generated"
    print_status "HTML report: htmlcov/index.html"
    
    # Check coverage
    COVERAGE=$(pytest --cov=src --cov-report=term-missing -q tests/ 2>&1 | grep "TOTAL" | awk '{print $NF}' | sed 's/%//')
    if [ -n "$COVERAGE" ]; then
        COVERAGE_INT=${COVERAGE%.*}
        if [ "$COVERAGE_INT" -ge 80 ]; then
            print_status "Coverage: ${COVERAGE}% (meets 80% requirement)"
        else
            print_warning "Coverage: ${COVERAGE}% (below 80% requirement)"
            TESTS_FAILED=1
        fi
    fi
else
    print_error "Coverage report generation failed"
    TESTS_FAILED=1
fi

# Final summary
print_status ""
print_status "=================================="
if [ $TESTS_FAILED -eq 0 ]; then
    print_status "All tests passed!"
    print_status "Coverage report: htmlcov/index.html"
    exit 0
else
    print_error "Some tests failed. Check output above."
    exit 1
fi

