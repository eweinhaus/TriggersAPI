#!/bin/bash
# Setup CloudWatch dashboard for Triggers API

set -e

DASHBOARD_NAME="${DASHBOARD_NAME:-TriggersAPI-Dashboard}"
REGION="${AWS_REGION:-us-east-1}"
DASHBOARD_FILE="${DASHBOARD_FILE:-scripts/cloudwatch_dashboard.json}"

echo "Creating CloudWatch dashboard: $DASHBOARD_NAME"
echo "Region: $REGION"
echo "Dashboard file: $DASHBOARD_FILE"

if [ ! -f "$DASHBOARD_FILE" ]; then
    echo "Error: Dashboard file not found: $DASHBOARD_FILE"
    exit 1
fi

# Create or update dashboard
aws cloudwatch put-dashboard \
    --dashboard-name "$DASHBOARD_NAME" \
    --dashboard-body "file://$DASHBOARD_FILE" \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo "Dashboard created/updated successfully"
    echo "View dashboard at: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=$DASHBOARD_NAME"
else
    echo "Error: Failed to create dashboard"
    exit 1
fi


