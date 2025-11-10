# Phase 2: AWS Infrastructure & Deployment - PRD

**Phase:** 2 of 6  
**Priority:** P0 (Must Have)  
**Estimated Duration:** 2-3 hours  
**Dependencies:** Phase 1 (Core API Backend)

---

## 1. Executive Summary

Phase 2 deploys the Phase 1 API to AWS, making it accessible via API Gateway. This phase includes SAM template creation, Lambda function configuration, DynamoDB table setup, IAM roles, CloudWatch logging, and CORS configuration.

**Goal:** API deployed and accessible on AWS via API Gateway URL.

---

## 2. Scope

### In Scope
- AWS SAM template with all resources
- Lambda function configuration
- API Gateway REST API setup
- DynamoDB tables (Events, API Keys)
- IAM roles and policies
- CloudWatch logging configuration
- CORS configuration for frontend
- Environment variables
- Deployment scripts and documentation

### Out of Scope
- Comprehensive testing (Phase 3)
- P1 features (Phase 4)
- Documentation (Phase 5)
- Frontend (Phase 6)
- Rate limiting (use API Gateway throttling if needed)

---

## 3. Functional Requirements

### 3.1 AWS SAM Template

**Required Resources:**
1. **Lambda Function**
   - Runtime: Python 3.11
   - Handler: `src.main.handler` (Mangum adapter for FastAPI)
   - Environment variables
   - IAM role with DynamoDB permissions

2. **API Gateway REST API**
   - REST API type
   - CORS configuration
   - Integration with Lambda
   - Stage: `prod` (or configurable)

3. **DynamoDB Tables**
   - Events table with GSI
   - API Keys table
   - On-demand billing mode

4. **CloudWatch Log Group**
   - For Lambda function logs
   - Retention: 7 days (configurable)

### 3.2 Lambda Function Configuration

**Handler:**
- Use Mangum adapter to wrap FastAPI app
- Handler function: `handler = Mangum(app)`
- Package FastAPI app with dependencies

**Environment Variables:**
- `DYNAMODB_TABLE_EVENTS`: Table name for events
- `DYNAMODB_TABLE_KEYS`: Table name for API keys
- `AWS_REGION`: AWS region (e.g., `us-east-1`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `AUTH_MODE`: Authentication mode (`local` for hardcoded key, `aws` for DynamoDB) - defaults to `aws` in production

**Memory & Timeout:**
- Memory: 512 MB (default, adjustable)
- Timeout: 30 seconds (default, adjustable)

### 3.3 API Gateway Configuration

**REST API:**
- Type: REST API (not HTTP API for better control)
- Endpoints (all with /v1 prefix):
  - `GET /v1/health` (health check)
  - `POST /v1/events`
  - `GET /v1/inbox`
  - `POST /v1/events/{event_id}/ack`
  - `DELETE /v1/events/{event_id}`
  - `GET /docs` (FastAPI auto-generated OpenAPI docs)

**CORS Configuration:**
- Allow origins: `*` (for MVP, restrict in production)
- Allow methods: `GET, POST, DELETE, OPTIONS`
- Allow headers: `Content-Type, X-API-Key, X-Request-ID`
- Max age: 3600

**Integration:**
- Lambda proxy integration
- All routes proxy to Lambda function
- FastAPI handles routing internally

### 3.4 DynamoDB Tables

**Events Table:**
- Table Name: `triggers-api-events-{stage}` (e.g., `triggers-api-events-prod`)
- Partition Key: `event_id` (String)
- Sort Key: `created_at` (String, ISO 8601)
- Billing Mode: On-demand
- Point-in-time recovery: Disabled (for MVP)
- Encryption: AWS managed keys
- **Note:** For MVP, no scaling concerns. This schema is sufficient for low-to-moderate volume.

**Inbox GSI:**
- Index Name: `status-created_at-index`
- Partition Key: `status` (String)
- Sort Key: `created_at` (String, ISO 8601)
- Projection: All attributes
- **Note:** For MVP scale, this GSI design is sufficient. No sharding needed.

**API Keys Table:**
- Table Name: `triggers-api-keys-{stage}`
- Partition Key: `api_key` (String)
- Billing Mode: On-demand
- Encryption: AWS managed keys

### 3.5 IAM Roles & Policies

**Lambda Execution Role:**
- Trust policy for Lambda service
- Permissions:
  - `dynamodb:PutItem` on Events table
  - `dynamodb:GetItem` on Events table
  - `dynamodb:UpdateItem` on Events table
  - `dynamodb:DeleteItem` on Events table
  - `dynamodb:Query` on Events table and GSI
  - `dynamodb:GetItem` on API Keys table
  - `logs:CreateLogGroup` (if needed)
  - `logs:CreateLogStream`
  - `logs:PutLogEvents`

**Principle of Least Privilege:**
- Only grant necessary permissions
- Scope to specific tables
- No wildcard permissions

### 3.6 CloudWatch Logging

**Log Group:**
- Name: `/aws/lambda/triggers-api-{stage}`
- Retention: 7 days (configurable)
- Structured logging format

**Logging Requirements:**
- Log all API requests with request ID (from X-Request-ID header or generated)
- Log errors with stack traces and request IDs
- Log DynamoDB operations (debug level)
- Include request ID in all log entries for correlation
- Exclude sensitive data (API keys, payloads in production)

---

## 4. Technical Requirements

### 4.1 SAM Template Structure

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Zapier Triggers API

Parameters:
  Stage:
    Type: String
    Default: prod
    Description: Deployment stage

Globals:
  Function:
    Runtime: python3.11
    Timeout: 30
    MemorySize: 512
    Environment:
      Variables:
        STAGE: !Ref Stage
        DYNAMODB_TABLE_EVENTS: !Ref EventsTable
        DYNAMODB_TABLE_KEYS: !Ref ApiKeysTable
        AWS_REGION: !Ref AWS::Region

Resources:
  # Lambda Function
  TriggersApiFunction:
    Type: AWS::Serverless::Function
    # ... configuration

  # API Gateway
  TriggersApi:
    Type: AWS::Serverless::Api
    # ... configuration

  # DynamoDB Tables
  EventsTable:
    Type: AWS::DynamoDB::Table
    # ... configuration

  ApiKeysTable:
    Type: AWS::DynamoDB::Table
    # ... configuration

Outputs:
  ApiUrl:
    Description: API Gateway endpoint URL
    Value: !Sub https://${TriggersApi}.execute-api.${AWS::Region}.amazonaws.com/${Stage}
```

### 4.2 Dependencies Update

**Additional Python Packages:**
- `mangum>=0.17.0` (FastAPI to Lambda adapter)

**Build Requirements:**
- AWS SAM CLI installed
- Docker (for SAM build)
- AWS CLI configured

### 4.3 Code Changes Required

**Handler Function:**
```python
# src/main.py
from mangum import Mangum
from fastapi import FastAPI

app = FastAPI(title="Zapier Triggers API")

# ... existing endpoints ...

# Lambda handler
handler = Mangum(app, lifespan="off")
```

**Database Configuration:**
- Update `src/database.py` to use environment variables
- Remove hardcoded DynamoDB endpoint (use AWS service)
- Use table names from environment variables

**API Key Migration:**
- Update `src/auth.py` to support both `AUTH_MODE=local` and `AUTH_MODE=aws`
- When `AUTH_MODE=aws`, query DynamoDB `triggers-api-keys` table
- When `AUTH_MODE=local`, use hardcoded key (for local development)
- Default to `aws` mode in production (set via environment variable)
- Migration path:
  1. Phase 1: Hardcoded key in `src/auth.py`
  2. Phase 2: Add `AUTH_MODE` environment variable support
  3. Phase 2: Update auth to check `AUTH_MODE` and route accordingly
  4. Phase 2: Use `scripts/seed_api_keys.py` to create production API keys in DynamoDB
  5. Phase 2: Set `AUTH_MODE=aws` in Lambda environment variables
- **Note:** For MVP, no API key caching needed. Direct DynamoDB lookup is sufficient.

### 4.4 Deployment Process

**Build:**
```bash
sam build
```

**Deploy:**
```bash
sam deploy --guided  # First time
sam deploy           # Subsequent deployments
```

**Parameters:**
- Stack name: `triggers-api`
- Region: `us-east-1` (or preferred)
- Confirm changes: Yes
- Allow SAM CLI IAM role creation: Yes
- Save arguments to config: Yes

---

## 5. Implementation Steps

1. **Update Code for Lambda**
   - Add Mangum adapter to `src/main.py`
   - Update database configuration for AWS
   - Update environment variable handling
   - Migrate API key authentication from hardcoded to DynamoDB
   - Add `AUTH_MODE` environment variable support
   - Test locally with Mangum

2. **Create SAM Template**
   - Define Lambda function resource
   - Define API Gateway resource
   - Define DynamoDB tables
   - Define IAM roles and policies
   - Define CloudWatch log group

3. **Configure API Gateway**
   - Set up REST API
   - Configure CORS
   - Set up Lambda integration
   - Configure routes

4. **Set Up DynamoDB**
   - Define Events table schema
   - Define Inbox GSI
   - Define API Keys table
   - Configure billing mode

5. **IAM Configuration**
   - Create Lambda execution role
   - Define least-privilege policies
   - Test permissions

6. **CloudWatch Setup**
   - Configure log group
   - Set retention policy
   - Test logging

7. **Deployment Scripts**
   - Create deployment documentation
   - Test SAM build locally
   - Test SAM deploy to AWS

8. **API Key Migration**
   - Run `scripts/seed_api_keys.py` to create production API keys
   - Verify API keys are stored in DynamoDB
   - Test authentication with DynamoDB-stored keys
   - Verify `AUTH_MODE=aws` works correctly

9. **Testing**
   - Test all endpoints via API Gateway URL (with /v1 prefix)
   - Verify DynamoDB operations
   - Check CloudWatch logs (with request IDs)
   - Test CORS configuration
   - Test health check endpoint

9. **Documentation**
   - Update README with deployment steps
   - Document API Gateway URL
   - Document environment variables

---

## 6. Success Criteria

- [ ] SAM template complete and validated
- [ ] API deployed to AWS successfully
- [ ] All endpoints accessible via API Gateway URL (with /v1 prefix)
- [ ] DynamoDB tables created with correct schema (created_at, not timestamp)
- [ ] API key migration from hardcoded to DynamoDB complete
- [ ] CloudWatch logs working with request IDs
- [ ] CORS configured correctly (including X-Request-ID header)
- [ ] IAM roles have correct permissions
- [ ] Can test all endpoints via API Gateway
- [ ] Health check endpoint accessible
- [ ] Environment variables configured correctly (including AUTH_MODE)
- [ ] Deployment process documented

---

## 7. Testing Strategy

### Deployment Testing
1. **SAM Build:**
   - Verify build succeeds
   - Check for missing dependencies
   - Verify Lambda package size

2. **SAM Deploy:**
   - Verify deployment succeeds
   - Check CloudFormation stack status
   - Verify all resources created

3. **API Gateway Testing:**
   - Test all endpoints via API Gateway URL (with /v1 prefix)
   - Test health check endpoint (GET /v1/health)
   - Verify CORS headers (including X-Request-ID)
   - Test OPTIONS requests
   - Verify error responses include request IDs

4. **DynamoDB Testing:**
   - Verify tables created
   - Test event creation
   - Test inbox query
   - Test acknowledgment

5. **CloudWatch Testing:**
   - Verify logs are created
   - Check log format
   - Verify request IDs

### Test Commands
```bash
# Get API URL
aws cloudformation describe-stacks --stack-name triggers-api --query 'Stacks[0].Outputs'

# Test health check
curl https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/v1/health

# Test endpoint (with /v1 prefix)
curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/v1/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -H "X-Request-ID: test-request-123" \
  -d '{"source": "test", "event_type": "test.created", "payload": {}}'
```

---

## 8. Known Limitations (Phase 2)

- No comprehensive testing (Phase 3)
- Basic error handling (enhanced in Phase 3)
- No rate limiting (use API Gateway throttling if needed)
- CORS allows all origins (restrict in production)
- No custom domain (use API Gateway default)
- No API key management UI (manual for MVP)
- No API key caching (direct DynamoDB lookup - sufficient for MVP)
- No scaling optimizations (not needed for MVP)

---

## 9. Cost Considerations

**AWS Free Tier:**
- Lambda: 1M requests/month free
- API Gateway: 1M requests/month free (first 12 months)
- DynamoDB: 25 GB storage, 25 RCU/WCU free

**Estimated Monthly Cost (Low Traffic - MVP):**
- Lambda: $0 (within free tier)
- API Gateway: $0 (within free tier)
- DynamoDB: $0-5 (depending on usage, on-demand billing)
- CloudWatch: $0-2 (logs, 7-day retention)

**Cost Optimization:**
- Use on-demand DynamoDB billing
- Set CloudWatch log retention to 7 days
- Monitor usage with AWS Cost Explorer

---

## 10. Security Considerations

**API Keys:**
- Store in DynamoDB (encrypted at rest)
- Never log API keys
- Use HTTPS only (API Gateway default)

**IAM:**
- Least privilege principle
- No wildcard permissions
- Separate roles for different functions

**Data:**
- DynamoDB encryption at rest (default)
- TLS 1.2+ for data in transit (API Gateway default)
- No PII in logs

---

## 11. Troubleshooting

### Common Issues

1. **Lambda Timeout:**
   - Increase timeout in SAM template
   - Check DynamoDB query performance
   - Optimize code

2. **CORS Errors:**
   - Verify CORS configuration in SAM template
   - Check API Gateway settings
   - Test with browser console

3. **DynamoDB Permissions:**
   - Verify IAM role permissions
   - Check table names match environment variables
   - Test with AWS CLI

4. **Deployment Failures:**
   - Check CloudFormation events
   - Verify IAM permissions for SAM
   - Check resource limits

---

## 12. Next Steps

After Phase 2 completion:
- Proceed to Phase 3: Testing & Error Handling
- Add comprehensive unit and integration tests
- Enhance error handling
- Standardize error responses

---

**Phase Status:** Not Started  
**Completion Date:** TBD

