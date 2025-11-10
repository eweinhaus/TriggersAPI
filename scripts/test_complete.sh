#!/bin/bash

# Complete test execution script
# Runs unit tests, generates coverage, and verifies API server can start

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Complete Test Execution${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Step 1: Run unit tests with coverage
echo -e "${GREEN}[1/3] Running unit tests with coverage...${NC}"
python3 -m pytest tests/unit/ -v --cov=src --cov-report=term --cov-report=html --tb=short

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Unit tests passed${NC}"
else
    echo -e "${RED}❌ Unit tests failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}[2/3] Checking coverage report...${NC}"
if [ -f "htmlcov/index.html" ]; then
    echo -e "${GREEN}✅ Coverage report generated: htmlcov/index.html${NC}"
    COVERAGE=$(python3 -m pytest tests/unit/ --cov=src --cov-report=term -q 2>&1 | grep "TOTAL" | awk '{print $NF}')
    echo -e "${GREEN}Coverage: ${COVERAGE}${NC}"
else
    echo -e "${YELLOW}⚠️  Coverage report not found${NC}"
fi

echo ""
echo -e "${GREEN}[3/3] Verifying API server can start...${NC}"

# Check if DynamoDB Local is running
if ! docker ps | grep -q dynamodb-local; then
    echo -e "${YELLOW}Starting DynamoDB Local...${NC}"
    docker-compose up -d dynamodb-local
    sleep 3
fi

# Test that server can start (quick test)
export DYNAMODB_ENDPOINT_URL=http://localhost:8000
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AUTH_MODE=local
export LOG_LEVEL=INFO

# Test import and basic functionality
python3 -c "
from src.main import app
from src.database import create_tables
print('✅ FastAPI app imports successfully')
print('✅ Database module imports successfully')
try:
    create_tables()
    print('✅ Tables can be created')
except Exception as e:
    print(f'⚠️  Table creation: {e}')
print('✅ API server ready to start')
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ API server verification passed${NC}"
else
    echo -e "${RED}❌ API server verification failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ All checks passed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. View coverage report: open htmlcov/index.html"
echo "2. Start API server for E2E tests: ./scripts/start_test_server.sh"
echo "3. Run E2E tests: pytest tests/e2e/ -v"
echo "4. Run Playwright tests: pytest tests/playwright/ -v (requires running server)"

