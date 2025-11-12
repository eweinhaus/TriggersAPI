#!/bin/bash
# Run k6 load tests

set -e

SCENARIO="${1:-event_ingestion}"
ENVIRONMENT="${2:-local}"
CONFIG_FILE="${CONFIG_FILE:-tests/load/config.yaml}"

echo "Running load test scenario: $SCENARIO"
echo "Environment: $ENVIRONMENT"

# Safety check for production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "WARNING: You are about to run load tests against PRODUCTION!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Aborted."
        exit 1
    fi
    # Limit production test duration
    export K6_DURATION_LIMIT="5m"
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set API URL and key based on environment
case $ENVIRONMENT in
    local)
        export API_URL="${LOCAL_API_URL:-http://localhost:8080}"
        export API_KEY="${LOCAL_API_KEY:-test-api-key-12345}"
        ;;
    staging)
        if [ -z "$STAGING_API_URL" ] || [ -z "$STAGING_API_KEY" ]; then
            echo "Error: STAGING_API_URL and STAGING_API_KEY must be set"
            exit 1
        fi
        export API_URL="$STAGING_API_URL"
        export API_KEY="$STAGING_API_KEY"
        ;;
    production)
        if [ -z "$PRODUCTION_API_URL" ] || [ -z "$PRODUCTION_API_KEY" ]; then
            echo "Error: PRODUCTION_API_URL and PRODUCTION_API_KEY must be set"
            exit 1
        fi
        export API_URL="$PRODUCTION_API_URL"
        export API_KEY="$PRODUCTION_API_KEY"
        ;;
    *)
        echo "Error: Unknown environment: $ENVIRONMENT"
        echo "Valid environments: local, staging, production"
        exit 1
        ;;
esac

echo "API URL: $API_URL"
echo "API Key: ${API_KEY:0:10}..."

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo "Error: k6 is not installed"
    echo "Install k6: https://k6.io/docs/getting-started/installation/"
    exit 1
fi

# Run the test scenario
SCENARIO_FILE="tests/load/scenarios/${SCENARIO}.js"

if [ ! -f "$SCENARIO_FILE" ]; then
    echo "Error: Scenario file not found: $SCENARIO_FILE"
    echo "Available scenarios:"
    ls -1 tests/load/scenarios/*.js | xargs -n1 basename | sed 's/.js$//'
    exit 1
fi

echo "Running scenario: $SCENARIO_FILE"
k6 run --out json=results_${SCENARIO}_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).json "$SCENARIO_FILE"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Load test completed successfully"
else
    echo "Load test failed or thresholds not met"
    exit $EXIT_CODE
fi


