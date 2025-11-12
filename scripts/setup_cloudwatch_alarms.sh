#!/bin/bash
# Setup CloudWatch alarms for Triggers API

set -e

REGION="${AWS_REGION:-us-east-1}"
NAMESPACE="${CLOUDWATCH_NAMESPACE:-TriggersAPI/Production}"
SNS_TOPIC_ARN="${SNS_TOPIC_ARN:-}"

echo "Setting up CloudWatch alarms"
echo "Region: $REGION"
echo "Namespace: $NAMESPACE"

# Function to create alarm
create_alarm() {
    local alarm_name=$1
    local metric_name=$2
    local threshold=$3
    local comparison=$4
    local evaluation_periods=${5:-2}
    local dimensions=${6:-""}
    
    echo "Creating alarm: $alarm_name"
    
    local alarm_cmd="aws cloudwatch put-metric-alarm \
        --alarm-name \"$alarm_name\" \
        --alarm-description \"$alarm_name\" \
        --metric-name \"$metric_name\" \
        --namespace \"$NAMESPACE\" \
        --statistic Average \
        --period 300 \
        --evaluation-periods $evaluation_periods \
        --threshold $threshold \
        --comparison-operator $comparison \
        --region $REGION"
    
    if [ -n "$dimensions" ]; then
        alarm_cmd="$alarm_cmd --dimensions $dimensions"
    fi
    
    if [ -n "$SNS_TOPIC_ARN" ]; then
        alarm_cmd="$alarm_cmd --alarm-actions $SNS_TOPIC_ARN"
    fi
    
    eval $alarm_cmd
    
    if [ $? -eq 0 ]; then
        echo "Alarm created: $alarm_name"
    else
        echo "Error: Failed to create alarm: $alarm_name"
        return 1
    fi
}

# Create alarms for each endpoint
ENDPOINTS=(
    "/v1/events:POST"
    "/v1/events/{event_id}:GET"
    "/v1/events/{event_id}/ack:POST"
    "/v1/events/{event_id}:DELETE"
    "/v1/inbox:GET"
    "/v1/health:GET"
)

for endpoint_method in "${ENDPOINTS[@]}"; do
    IFS=':' read -r endpoint method <<< "$endpoint_method"
    endpoint_safe=$(echo "$endpoint" | tr '/{}' '_' | tr -d ' ')
    alarm_name="TriggersAPI-${endpoint_safe}-${method}-HighLatency"
    dimensions="Name=Endpoint,Value=$endpoint Name=Method,Value=$method"
    
    create_alarm "$alarm_name" "ApiLatency" 100 "GreaterThanThreshold" 2 "$dimensions"
done

# Create success rate alarm (aggregate)
create_alarm "TriggersAPI-LowSuccessRate" "ApiRequestCount" 99.9 "LessThanThreshold" 2 "Name=Status,Value=success"

# Create error rate alarm (aggregate)
create_alarm "TriggersAPI-HighErrorRate" "ApiErrorRate" 0.1 "GreaterThanThreshold" 2 ""

echo "All alarms created successfully"
echo "View alarms at: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#alarmsV2:"


