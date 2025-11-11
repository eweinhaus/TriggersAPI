#!/bin/bash

# Monitor GSI creation progress
TABLE_NAME="triggers-api-events-prod"
REGION="us-east-1"
GSI_NAME="event-id-index"

echo "Monitoring GSI creation for table: $TABLE_NAME"
echo "Press Ctrl+C to stop monitoring"
echo "=========================================="
echo ""

START_TIME=$(date +%s)

while true; do
  CURRENT_TIME=$(date -u +%Y-%m-%dT%H:%M:%S)
  ELAPSED=$(( $(date +%s) - START_TIME ))
  ELAPSED_MIN=$(( ELAPSED / 60 ))
  ELAPSED_SEC=$(( ELAPSED % 60 ))
  
  # Get GSI status
  GSI_STATUS=$(aws dynamodb describe-table \
    --table-name "$TABLE_NAME" \
    --region "$REGION" \
    --query 'Table.GlobalSecondaryIndexes[?IndexName==`'"$GSI_NAME"'`].IndexStatus' \
    --output text 2>/dev/null)
  
  # Get latest progress from CloudWatch
  PROGRESS_JSON=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/DynamoDB \
    --metric-name OnlineIndexPercentageProgress \
    --dimensions Name=TableName,Value="$TABLE_NAME" Name=GlobalSecondaryIndexName,Value="$GSI_NAME" \
    --start-time $(date -u -v-10M +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 60 \
    --statistics Average \
    --region "$REGION" \
    --output json 2>/dev/null)
  
  PROGRESS=$(echo "$PROGRESS_JSON" | jq -r '.Datapoints | sort_by(.Timestamp) | .[-1] | if . then "\(.Average)%" else "N/A" end')
  PROGRESS_TIME=$(echo "$PROGRESS_JSON" | jq -r '.Datapoints | sort_by(.Timestamp) | .[-1] | if . then .Timestamp else "N/A" end')
  
  # Clear line and print status
  printf "\r[%02d:%02d elapsed] Status: %-10s | Progress: %-8s (last update: %s)" \
    "$ELAPSED_MIN" "$ELAPSED_SEC" "$GSI_STATUS" "$PROGRESS" "${PROGRESS_TIME:11:5}"
  
  if [ "$GSI_STATUS" = "ACTIVE" ]; then
    echo ""
    echo ""
    echo "✓✓✓ GSI is now ACTIVE! Creation complete. ✓✓✓"
    break
  fi
  
  sleep 30
done

