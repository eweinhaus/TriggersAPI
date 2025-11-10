# Phase 2: AWS Infrastructure & Deployment - Task List

**Phase:** 2 of 6  
**Priority:** P0 (Must Have)  
**Status:** Not Started  
**Created:** 2024-01-XX  
**Dependencies:** Phase 1 (Core API Backend) must be complete

---

## Overview

This task list covers the deployment of the Phase 1 API to AWS, making it accessible via API Gateway. The goal is to deliver a fully deployed API on AWS with Lambda, API Gateway, DynamoDB, IAM roles, CloudWatch logging, and CORS configuration.

**Key Deliverables:**
- AWS SAM template with all infrastructure resources
- Lambda function configured with Mangum adapter
- API Gateway REST API with CORS
- Production DynamoDB tables (Events with GSI, API Keys)
- IAM roles with least-privilege permissions
- CloudWatch log group with retention policy
- API key authentication migrated from hardcoded to DynamoDB
- Deployment process documented and working

---

## Task Breakdown

### 1. Code Updates for Lambda Deployment

#### 1.1 Add Mangum Dependency
- [ ] Update `requirements.txt` to include `mangum>=0.17.0`
- [ ] Install dependency locally: `pip install mangum>=0.17.0`
- [ ] Verify dependency is compatible with FastAPI version

#### 1.2 Update Main Application for Lambda
- [ ] Open `src/main.py`
- [ ] Import Mangum: `from mangum import Mangum`
- [ ] Create Lambda handler after FastAPI app initialization:
  ```python
  handler = Mangum(app, lifespan="off")
  ```
- [ ] Ensure handler is at module level (not inside function)
- [ ] Test locally that app still works with uvicorn (handler should not interfere)

#### 1.3 Update Database Configuration for AWS
- [ ] Open `src/database.py`
- [ ] Update DynamoDB client initialization:
  - Read `DYNAMODB_ENDPOINT_URL` from environment (for local dev)
  - If `DYNAMODB_ENDPOINT_URL` is not set, use AWS service (production)
  - Read `AWS_REGION` from environment (default: `us-east-1`)
  - Remove hardcoded endpoint URL for production
- [ ] Update table name references:
  - Read `DYNAMODB_TABLE_EVENTS` from environment
  - Read `DYNAMODB_TABLE_KEYS` from environment
  - Use these in all DynamoDB operations
- [ ] Ensure table creation functions use environment variables
- [ ] Test database connection works both locally (with endpoint) and in AWS (without endpoint)

#### 1.4 Update API Key Authentication for DynamoDB
- [ ] Open `src/auth.py`
- [ ] Read `AUTH_MODE` from environment (default: `local` for backward compatibility)
- [ ] Implement dual-mode authentication:
  - **Local mode (`AUTH_MODE=local`):**
    - Use hardcoded key `test-api-key-12345` (for local development)
    - Maintain backward compatibility with Phase 1
  - **AWS mode (`AUTH_MODE=aws`):**
    - Query DynamoDB `triggers-api-keys-{stage}` table
    - Use `DYNAMODB_TABLE_KEYS` environment variable for table name
    - Check if API key exists and `is_active` is `True`
    - Return API key if valid, raise exception if invalid
- [ ] Handle DynamoDB errors gracefully (ResourceNotFoundException, etc.)
- [ ] Ensure no API keys are logged (security)
- [ ] Test both modes work correctly

#### 1.5 Update Environment Variable Handling
- [ ] Review all environment variable usage:
  - `DYNAMODB_TABLE_EVENTS` (required in AWS)
  - `DYNAMODB_TABLE_KEYS` (required in AWS)
  - `AWS_REGION` (required, default: `us-east-1`)
  - `AUTH_MODE` (optional, default: `local`)
  - `LOG_LEVEL` (optional, default: `INFO`)
  - `DYNAMODB_ENDPOINT_URL` (optional, only for local dev)
- [ ] Ensure all environment variables have sensible defaults where appropriate
- [ ] Add validation for required variables in AWS mode

#### 1.6 Test Locally with Mangum (Optional)
- [ ] Create test script to verify Mangum adapter works:
  ```python
  from mangum import Mangum
  from src.main import app
  handler = Mangum(app, lifespan="off")
  # Test handler can be called
  ```
- [ ] Verify FastAPI app still works with uvicorn for local development

---

### 2. AWS SAM Template Creation

#### 2.1 Create SAM Template File
- [ ] Create `template.yaml` in project root
- [ ] Add template header:
  ```yaml
  AWSTemplateFormatVersion: '2010-09-09'
  Transform: AWS::Serverless-2016-10-31
  Description: Zapier Triggers API
  ```

#### 2.2 Define Template Parameters
- [ ] Add `Parameters` section:
  - `Stage`: String, default `prod`, description "Deployment stage"
- [ ] Document parameter usage

#### 2.3 Configure Global Function Settings
- [ ] Add `Globals` section:
  - `Function.Runtime`: `python3.11`
  - `Function.Timeout`: `30`
  - `Function.MemorySize`: `512`
  - `Function.Environment.Variables`:
    - `STAGE`: `!Ref Stage`
    - `DYNAMODB_TABLE_EVENTS`: `!Ref EventsTable`
    - `DYNAMODB_TABLE_KEYS`: `!Ref ApiKeysTable`
    - `AWS_REGION`: `!Ref AWS::Region`
    - `AUTH_MODE`: `aws` (production mode)
    - `LOG_LEVEL`: `INFO`

#### 2.4 Define Lambda Function Resource
- [ ] Add `TriggersApiFunction` resource:
  - Type: `AWS::Serverless::Function`
  - Handler: `src.main.handler` (Mangum handler)
  - CodeUri: `src/` (or use build configuration)
  - Description: "Zapier Triggers API Lambda function"
  - Runtime: `python3.11` (inherit from Globals)
  - Timeout: `30` (inherit from Globals)
  - MemorySize: `512` (inherit from Globals)
  - Environment variables (inherit from Globals, can override if needed)
  - Policies:
    - DynamoDB read/write permissions (see IAM section)
    - CloudWatch logs permissions
  - Events:
    - API Gateway proxy event (see API Gateway section)

#### 2.5 Define API Gateway Resource
- [ ] Add `TriggersApi` resource:
  - Type: `AWS::Serverless::Api`
  - StageName: `!Ref Stage`
  - DefinitionUri: Use inline definition or OpenAPI spec
  - Cors:
    - AllowMethods: `GET, POST, DELETE, OPTIONS`
    - AllowHeaders: `Content-Type, X-API-Key, X-Request-ID`
    - AllowOrigin: `*` (for MVP, restrict in production)
    - MaxAge: `3600`
  - EndpointConfiguration:
    - Type: `REGIONAL` (or `EDGE` if preferred)
  - Auth: None (authentication handled in Lambda)

#### 2.6 Define DynamoDB Events Table
- [ ] Add `EventsTable` resource:
  - Type: `AWS::DynamoDB::Table`
  - TableName: `!Sub triggers-api-events-${Stage}`
  - BillingMode: `PAY_PER_REQUEST` (on-demand)
  - AttributeDefinitions:
    - `event_id`: `S` (String)
    - `created_at`: `S` (String)
    - `status`: `S` (String) (for GSI)
  - KeySchema:
    - PartitionKey: `event_id` (String)
    - SortKey: `created_at` (String)
  - GlobalSecondaryIndexes:
    - IndexName: `status-created_at-index`
      - KeySchema:
        - PartitionKey: `status` (String)
        - SortKey: `created_at` (String)
      - Projection:
        - ProjectionType: `ALL`
  - TimeToLiveSpecification:
    - AttributeName: `ttl`
    - Enabled: `true`
  - SSESpecification:
    - SSEEnabled: `true` (AWS managed keys, default)
  - DeletionPolicy: `Retain` (optional, for safety)

#### 2.7 Define DynamoDB API Keys Table
- [ ] Add `ApiKeysTable` resource:
  - Type: `AWS::DynamoDB::Table`
  - TableName: `!Sub triggers-api-keys-${Stage}`
  - BillingMode: `PAY_PER_REQUEST` (on-demand)
  - AttributeDefinitions:
    - `api_key`: `S` (String)
  - KeySchema:
    - PartitionKey: `api_key` (String)
  - SSESpecification:
    - SSEEnabled: `true` (AWS managed keys, default)
  - DeletionPolicy: `Retain` (optional, for safety)

#### 2.8 Define CloudWatch Log Group
- [ ] Add `TriggersApiLogGroup` resource:
  - Type: `AWS::Logs::LogGroup`
  - LogGroupName: `!Sub /aws/lambda/triggers-api-${Stage}`
  - RetentionInDays: `7`
  - DeletionPolicy: `Delete` (optional, for cleanup)

#### 2.9 Define IAM Role and Policies
- [ ] Lambda execution role is created automatically by SAM
- [ ] Add explicit IAM policy for Lambda function:
  - DynamoDB permissions:
    - `dynamodb:PutItem` on Events table
    - `dynamodb:GetItem` on Events table
    - `dynamodb:UpdateItem` on Events table
    - `dynamodb:DeleteItem` on Events table
    - `dynamodb:Query` on Events table and GSI
    - `dynamodb:GetItem` on API Keys table
  - CloudWatch Logs permissions:
    - `logs:CreateLogGroup` (if needed)
    - `logs:CreateLogStream`
    - `logs:PutLogEvents`
- [ ] Use least-privilege principle (no wildcards)
- [ ] Scope permissions to specific table ARNs using `!GetAtt`

#### 2.10 Define API Gateway Event for Lambda
- [ ] In Lambda function `Events` section, add:
  - Type: `Api`
  - Properties:
    - RestApiId: `!Ref TriggersApi`
    - Path: `/{proxy+}` (catch-all for FastAPI routing)
    - Method: `ANY` (FastAPI handles routing internally)

#### 2.11 Define Template Outputs
- [ ] Add `Outputs` section:
  - `ApiUrl`:
    - Description: "API Gateway endpoint URL"
    - Value: `!Sub https://${TriggersApi}.execute-api.${AWS::Region}.amazonaws.com/${Stage}`
    - Export: Optional, for cross-stack references
  - `EventsTableName`:
    - Description: "DynamoDB Events table name"
    - Value: `!Ref EventsTable`
  - `ApiKeysTableName`:
    - Description: "DynamoDB API Keys table name"
    - Value: `!Ref ApiKeysTable`

#### 2.12 Validate SAM Template
- [ ] Run `sam validate` to check template syntax
- [ ] Fix any validation errors
- [ ] Review template for best practices

---

### 3. SAM Build Configuration

#### 3.1 Create SAM Build Configuration (Optional)
- [ ] Create `samconfig.toml` (will be created by `sam deploy --guided`)
- [ ] Or create manually with deployment parameters:
  - Stack name: `triggers-api`
  - Region: `us-east-1` (or preferred)
  - Confirm changes: `true`
  - Capabilities: `CAPABILITY_IAM` (for IAM role creation)

#### 3.2 Test SAM Build Locally
- [ ] Run `sam build` to build Lambda package
- [ ] Verify build succeeds without errors
- [ ] Check `.aws-sam/` directory is created
- [ ] Verify all dependencies are included in build
- [ ] Check Lambda package size (should be reasonable, < 50MB typically)

---

### 4. API Key Migration Script

#### 4.1 Create API Key Seeding Script
- [ ] Create or update `scripts/seed_api_keys.py`
- [ ] Implement function to create API keys in DynamoDB:
  - Accept API key value, source (optional), and stage
  - Create item in `triggers-api-keys-{stage}` table
  - Set `is_active: true`
  - Set `created_at` timestamp (ISO 8601)
  - Handle duplicate keys gracefully
- [ ] Support command-line arguments:
  - `--api-key`: API key value (required)
  - `--source`: Source identifier (optional)
  - `--stage`: Deployment stage (default: `prod`)
  - `--region`: AWS region (default: `us-east-1`)
- [ ] Add validation for API key format
- [ ] Add confirmation prompt for production keys

#### 4.2 Test API Key Seeding Script
- [ ] Test script locally with DynamoDB Local (if possible)
- [ ] Test script with AWS DynamoDB (after tables are created)
- [ ] Verify API keys are stored correctly
- [ ] Verify `is_active` flag is set

#### 4.3 Document API Key Management
- [ ] Document how to create API keys using script
- [ ] Document how to list API keys (AWS CLI command)
- [ ] Document how to deactivate API keys (manual DynamoDB update)
- [ ] Add security notes about API key management

---

### 5. Deployment Process

#### 5.1 Pre-Deployment Checklist
- [ ] Verify Phase 1 is complete and working locally
- [ ] Verify AWS CLI is installed and configured
- [ ] Verify SAM CLI is installed (`sam --version`)
- [ ] Verify Docker is running (required for SAM build)
- [ ] Verify AWS credentials have necessary permissions:
  - CloudFormation (create/update stacks)
  - Lambda (create/update functions)
  - API Gateway (create/update APIs)
  - DynamoDB (create tables)
  - IAM (create roles)
  - CloudWatch Logs (create log groups)
- [ ] Choose AWS region (e.g., `us-east-1`)
- [ ] Choose stack name (e.g., `triggers-api`)

#### 5.2 First-Time Deployment
- [ ] Run `sam build` to build Lambda package
- [ ] Run `sam deploy --guided`:
  - Stack name: `triggers-api`
  - AWS Region: `us-east-1` (or preferred)
  - Confirm changes before deploy: `Y`
  - Allow SAM CLI IAM role creation: `Y`
  - Disable rollback: `N` (default)
  - Save arguments to configuration file: `Y`
- [ ] Wait for CloudFormation stack creation (5-10 minutes)
- [ ] Note the API Gateway URL from outputs
- [ ] Save API Gateway URL for testing

#### 5.3 Subsequent Deployments
- [ ] Run `sam build` to rebuild package
- [ ] Run `sam deploy` (uses saved configuration)
- [ ] Verify deployment succeeds
- [ ] Check CloudFormation stack status

#### 5.4 Verify Deployment
- [ ] Check CloudFormation stack is `CREATE_COMPLETE` or `UPDATE_COMPLETE`
- [ ] Verify Lambda function exists and has correct handler
- [ ] Verify API Gateway API exists
- [ ] Verify DynamoDB tables exist with correct schema
- [ ] Verify CloudWatch log group exists
- [ ] Get API Gateway URL from stack outputs

---

### 6. API Key Setup in Production

#### 6.1 Create Production API Keys
- [ ] Run `scripts/seed_api_keys.py` to create production API keys:
  ```bash
  python scripts/seed_api_keys.py --api-key <your-api-key> --stage prod --region us-east-1
  ```
- [ ] Create at least one test API key for testing
- [ ] Verify API keys are stored in DynamoDB:
  ```bash
  aws dynamodb get-item --table-name triggers-api-keys-prod --key '{"api_key": {"S": "<your-api-key>"}}'
  ```

#### 6.2 Verify API Key Authentication
- [ ] Test API key lookup works in Lambda:
  - Make test request to deployed API
  - Verify authentication succeeds with DynamoDB-stored key
  - Verify authentication fails with invalid key
- [ ] Check CloudWatch logs for authentication attempts

---

### 7. Testing Deployed API

#### 7.1 Get API Gateway URL
- [ ] Retrieve API Gateway URL from CloudFormation outputs:
  ```bash
  aws cloudformation describe-stacks --stack-name triggers-api --query 'Stacks[0].Outputs'
  ```
- [ ] Or get from SAM outputs:
  ```bash
  sam list stack-outputs --stack-name triggers-api
  ```
- [ ] Save URL for testing (format: `https://<api-id>.execute-api.<region>.amazonaws.com/prod`)

#### 7.2 Test Health Check Endpoint
- [ ] Test `GET /v1/health`:
  ```bash
  curl https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/v1/health
  ```
- [ ] Verify 200 OK response
- [ ] Verify response format matches spec
- [ ] Verify no authentication required

#### 7.3 Test Event Ingestion Endpoint
- [ ] Test `POST /v1/events`:
  ```bash
  curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/v1/events \
    -H "Content-Type: application/json" \
    -H "X-API-Key: <your-api-key>" \
    -H "X-Request-ID: test-request-123" \
    -d '{"source": "test", "event_type": "test.created", "payload": {}}'
  ```
- [ ] Verify 201 Created response
- [ ] Verify `event_id` and `request_id` in response
- [ ] Verify event stored in DynamoDB
- [ ] Test error cases:
  - Missing API key → 401 Unauthorized
  - Invalid API key → 401 Unauthorized
  - Invalid payload → 400 Bad Request

#### 7.4 Test Inbox Endpoint
- [ ] Test `GET /v1/inbox`:
  ```bash
  curl -X GET "https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/v1/inbox?limit=10" \
    -H "X-API-Key: <your-api-key>"
  ```
- [ ] Verify 200 OK response with events
- [ ] Verify pagination works (if multiple events)
- [ ] Test filtering:
  - `?source=test`
  - `?event_type=test.created`
  - `?source=test&event_type=test.created`
- [ ] Verify `request_id` in response

#### 7.5 Test Acknowledge Endpoint
- [ ] Test `POST /v1/events/{event_id}/ack`:
  ```bash
  curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/v1/events/<event-id>/ack \
    -H "X-API-Key: <your-api-key>"
  ```
- [ ] Verify 200 OK response
- [ ] Verify event status updated to "acknowledged"
- [ ] Verify `acknowledged_at` timestamp set
- [ ] Test error cases:
  - Non-existent event → 404 Not Found
  - Already acknowledged → 409 Conflict

#### 7.6 Test Delete Endpoint
- [ ] Test `DELETE /v1/events/{event_id}`:
  ```bash
  curl -X DELETE https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/v1/events/<event-id> \
    -H "X-API-Key: <your-api-key>"
  ```
- [ ] Verify 200 OK response
- [ ] Verify event deleted from DynamoDB
- [ ] Test idempotency (delete non-existent event → 200 OK)

#### 7.7 Test CORS Configuration
- [ ] Test OPTIONS request:
  ```bash
  curl -X OPTIONS https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/v1/events \
    -H "Origin: https://example.com" \
    -H "Access-Control-Request-Method: POST"
  ```
- [ ] Verify CORS headers in response:
  - `Access-Control-Allow-Origin: *`
  - `Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS`
  - `Access-Control-Allow-Headers: Content-Type, X-API-Key, X-Request-ID`
  - `Access-Control-Max-Age: 3600`
- [ ] Test from browser console (if possible) to verify CORS works

#### 7.8 Test Request ID Tracking
- [ ] Test with provided `X-Request-ID` header:
  ```bash
  curl -X GET https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/v1/health \
    -H "X-Request-ID: custom-request-id-123"
  ```
- [ ] Verify response includes provided request ID
- [ ] Test without `X-Request-ID` header:
  ```bash
  curl -X GET https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/v1/health
  ```
- [ ] Verify response includes generated request ID (UUID v4)

---

### 8. CloudWatch Logging Verification

#### 8.1 Verify Log Group Created
- [ ] Check CloudWatch log group exists:
  ```bash
  aws logs describe-log-groups --log-group-name-prefix /aws/lambda/triggers-api
  ```
- [ ] Verify log group name: `/aws/lambda/triggers-api-prod`
- [ ] Verify retention is set to 7 days

#### 8.2 Check Lambda Logs
- [ ] View recent logs:
  ```bash
  aws logs tail /aws/lambda/triggers-api-prod --follow
  ```
- [ ] Or view in AWS Console: CloudWatch → Log groups → `/aws/lambda/triggers-api-prod`
- [ ] Verify logs include:
  - Request IDs in log entries
  - API request information
  - Error messages (if any)
  - DynamoDB operations (if LOG_LEVEL=DEBUG)

#### 8.3 Verify Request ID Correlation
- [ ] Make test API request with known request ID
- [ ] Check CloudWatch logs for that request ID
- [ ] Verify request ID appears in all related log entries
- [ ] Verify error logs include request ID

#### 8.4 Verify No Sensitive Data in Logs
- [ ] Review logs for API keys (should not appear)
- [ ] Review logs for sensitive payload data (should be sanitized in production)
- [ ] Verify only necessary information is logged

---

### 9. DynamoDB Verification

#### 9.1 Verify Tables Created
- [ ] List DynamoDB tables:
  ```bash
  aws dynamodb list-tables
  ```
- [ ] Verify `triggers-api-events-prod` exists
- [ ] Verify `triggers-api-keys-prod` exists

#### 9.2 Verify Events Table Schema
- [ ] Describe Events table:
  ```bash
  aws dynamodb describe-table --table-name triggers-api-events-prod
  ```
- [ ] Verify partition key: `event_id` (String)
- [ ] Verify sort key: `created_at` (String)
- [ ] Verify GSI `status-created_at-index` exists:
  - Partition key: `status` (String)
  - Sort key: `created_at` (String)
- [ ] Verify TTL attribute: `ttl` (enabled)
- [ ] Verify billing mode: `PAY_PER_REQUEST` (on-demand)

#### 9.3 Verify API Keys Table Schema
- [ ] Describe API Keys table:
  ```bash
  aws dynamodb describe-table --table-name triggers-api-keys-prod
  ```
- [ ] Verify partition key: `api_key` (String)
- [ ] Verify billing mode: `PAY_PER_REQUEST` (on-demand)

#### 9.4 Test DynamoDB Operations
- [ ] Create test event via API
- [ ] Query Events table directly:
  ```bash
  aws dynamodb get-item --table-name triggers-api-events-prod \
    --key '{"event_id": {"S": "<event-id>"}, "created_at": {"S": "<timestamp>"}}'
  ```
- [ ] Query Inbox GSI:
  ```bash
  aws dynamodb query --table-name triggers-api-events-prod \
    --index-name status-created_at-index \
    --key-condition-expression "status = :status" \
    --expression-attribute-values '{":status": {"S": "pending"}}'
  ```
- [ ] Verify operations work correctly

---

### 10. IAM Permissions Verification

#### 10.1 Verify Lambda Execution Role
- [ ] Get Lambda function configuration:
  ```bash
  aws lambda get-function --function-name triggers-api-prod-TriggersApiFunction-<id>
  ```
- [ ] Note the execution role ARN
- [ ] Describe the IAM role:
  ```bash
  aws iam get-role --role-name <role-name>
  ```
- [ ] List role policies:
  ```bash
  aws iam list-role-policies --role-name <role-name>
  aws iam list-attached-role-policies --role-name <role-name>
  ```

#### 10.2 Verify DynamoDB Permissions
- [ ] Check IAM policy includes:
  - `dynamodb:PutItem` on Events table
  - `dynamodb:GetItem` on Events table
  - `dynamodb:UpdateItem` on Events table
  - `dynamodb:DeleteItem` on Events table
  - `dynamodb:Query` on Events table and GSI
  - `dynamodb:GetItem` on API Keys table
- [ ] Verify permissions are scoped to specific table ARNs (not wildcards)
- [ ] Verify no unnecessary permissions

#### 10.3 Verify CloudWatch Logs Permissions
- [ ] Check IAM policy includes:
  - `logs:CreateLogGroup` (if needed)
  - `logs:CreateLogStream`
  - `logs:PutLogEvents`
- [ ] Verify permissions are scoped to specific log group (if possible)

---

### 11. Documentation Updates

#### 11.1 Update README
- [ ] Add AWS deployment section to README
- [ ] Document prerequisites:
  - AWS CLI installed and configured
  - SAM CLI installed
  - Docker running
  - AWS account with appropriate permissions
- [ ] Document deployment steps:
  - `sam build`
  - `sam deploy --guided` (first time)
  - `sam deploy` (subsequent)
- [ ] Document API Gateway URL retrieval
- [ ] Document API key management:
  - How to create API keys
  - How to list API keys
  - How to deactivate API keys
- [ ] Document environment variables:
  - Which are set automatically by SAM
  - Which can be overridden
- [ ] Add troubleshooting section:
  - Common deployment issues
  - How to check CloudFormation stack status
  - How to view CloudWatch logs
  - How to verify IAM permissions

#### 11.2 Document API Gateway URL
- [ ] Add API Gateway URL to README (or document how to retrieve it)
- [ ] Note that URL includes `/prod` stage prefix
- [ ] Document that all endpoints are accessible at `{api-url}/v1/...`

#### 11.3 Document Testing Commands
- [ ] Add example cURL commands for all endpoints using API Gateway URL
- [ ] Include example with API key
- [ ] Include example with request ID header
- [ ] Document how to test CORS

#### 11.4 Create Deployment Guide (Optional)
- [ ] Create `DEPLOYMENT.md` with detailed deployment instructions
- [ ] Include step-by-step guide for first-time deployment
- [ ] Include troubleshooting guide
- [ ] Include rollback procedures (if needed)

---

### 12. Cleanup and Optimization (Optional)

#### 12.1 Review CloudFormation Stack
- [ ] Review stack resources in AWS Console
- [ ] Verify no unnecessary resources
- [ ] Verify resource naming is consistent

#### 12.2 Review Costs
- [ ] Check AWS Cost Explorer for estimated costs
- [ ] Verify costs are within expected range (should be minimal for MVP)
- [ ] Document cost considerations

#### 12.3 Set Up Monitoring Alarms (Optional)
- [ ] Set up CloudWatch alarms for Lambda errors (optional for MVP)
- [ ] Set up alarms for API Gateway 5xx errors (optional for MVP)
- [ ] Document alarm configuration

---

## Success Criteria Checklist

- [ ] SAM template complete and validated (`sam validate` passes)
- [ ] API deployed to AWS successfully (CloudFormation stack `CREATE_COMPLETE`)
- [ ] All endpoints accessible via API Gateway URL (with /v1 prefix)
- [ ] DynamoDB tables created with correct schema:
  - Events table: partition key `event_id`, sort key `created_at`
  - Events table GSI: `status-created_at-index` with correct keys
  - API Keys table: partition key `api_key`
- [ ] API key migration from hardcoded to DynamoDB complete:
  - `AUTH_MODE=aws` works correctly
  - API keys stored in DynamoDB
  - Authentication works with DynamoDB-stored keys
- [ ] CloudWatch logs working with request IDs:
  - Log group created
  - Logs include request IDs
  - Request ID correlation works
- [ ] CORS configured correctly:
  - CORS headers present in responses
  - `X-Request-ID` header allowed
  - OPTIONS requests work
- [ ] IAM roles have correct permissions:
  - Least-privilege principle followed
  - DynamoDB permissions scoped to specific tables
  - CloudWatch logs permissions present
- [ ] Can test all endpoints via API Gateway:
  - Health check works
  - Event ingestion works
  - Inbox query works
  - Acknowledgment works
  - Delete works
- [ ] Environment variables configured correctly:
  - `AUTH_MODE=aws` set in Lambda
  - Table names match between code and template
  - Region configured correctly
- [ ] Deployment process documented:
  - README updated with deployment steps
  - API Gateway URL documented
  - API key management documented

---

## Notes & Considerations

### Mangum Adapter
- Mangum wraps FastAPI app to make it compatible with Lambda
- Use `lifespan="off"` to disable FastAPI lifespan events (not needed for Lambda)
- Handler must be at module level for Lambda to import it
- Test locally that uvicorn still works (Mangum handler shouldn't interfere)

### API Key Migration
- Support both `AUTH_MODE=local` and `AUTH_MODE=aws` during transition
- Local mode uses hardcoded key (for local development)
- AWS mode queries DynamoDB (for production)
- Default to `aws` mode in production (set via SAM template)
- Seed API keys in DynamoDB before testing

### CORS Configuration
- Configure in SAM template (API Gateway level)
- Also ensure FastAPI CORS middleware doesn't conflict (if added)
- Test from browser to verify CORS works
- For MVP, allow all origins (`*`); restrict in production

### Environment Variables
- SAM template sets environment variables automatically
- Table names use `!Ref` to reference DynamoDB table resources
- Region uses `!Ref AWS::Region` for automatic detection
- `AUTH_MODE` must be set to `aws` in production

### DynamoDB Table Names
- Include stage suffix: `triggers-api-events-{stage}`
- Match between SAM template and code
- Code reads from environment variables set by SAM

### IAM Permissions
- SAM creates Lambda execution role automatically
- Add explicit policies for DynamoDB and CloudWatch
- Use least-privilege principle (no wildcards)
- Scope permissions to specific table ARNs

### CloudWatch Logs
- Log group created automatically by SAM (or explicitly defined)
- Retention set to 7 days (configurable)
- Request IDs should be included in all log entries
- No sensitive data (API keys) in logs

### Testing Considerations
- API Gateway URL includes stage prefix (`/prod`)
- All endpoints accessible at `{api-url}/v1/...`
- Test with real API keys from DynamoDB
- CloudWatch logs may have slight delay (few seconds)

### Deployment Process
- First deployment takes 5-10 minutes (CloudFormation stack creation)
- Subsequent deployments are faster (updates only)
- Use `sam deploy --guided` first time to save configuration
- Use `sam deploy` for subsequent deployments

### Known Limitations (Phase 2)
- No comprehensive testing (Phase 3)
- Basic error handling (enhanced in Phase 3)
- No rate limiting (use API Gateway throttling if needed)
- CORS allows all origins (restrict in production)
- No custom domain (use API Gateway default)
- No API key management UI (manual for MVP)
- No API key caching (direct DynamoDB lookup - sufficient for MVP)

---

## Next Steps After Completion

After Phase 2 completion:
1. Proceed to Phase 3: Testing & Error Handling
2. Add comprehensive unit and integration tests
3. Enhance error handling
4. Standardize error responses
5. Add automated testing for deployed API

---

**Task List Status:** Ready for Implementation  
**Last Updated:** 2024-01-XX

