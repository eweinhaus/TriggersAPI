# Frontend Deployment Guide

This guide explains how to deploy the frontend dashboard to AWS S3 + CloudFront.

## Prerequisites

1. AWS CLI installed and configured
2. AWS credentials with permissions for:
   - S3 (read/write)
   - CloudFront (create invalidation)
3. S3 bucket created for frontend hosting
4. CloudFront distribution created (optional but recommended)

## Setup

### 1. Create S3 Bucket

```bash
aws s3 mb s3://triggers-api-frontend --region us-east-1
```

### 2. Configure S3 Bucket for Static Website Hosting

```bash
aws s3 website s3://triggers-api-frontend \
    --index-document index.html \
    --error-document index.html
```

### 3. Set Bucket Policy for Public Read Access

Create a file `bucket-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::triggers-api-frontend/*"
    }
  ]
}
```

Apply the policy:

```bash
aws s3api put-bucket-policy \
    --bucket triggers-api-frontend \
    --policy file://bucket-policy.json
```

### 4. Create CloudFront Distribution (Optional but Recommended)

1. Go to AWS CloudFront Console
2. Create a new distribution
3. Set origin to your S3 bucket
4. Set default root object to `index.html`
5. Configure error pages:
   - 403 → 200 → `/index.html`
   - 404 → 200 → `/index.html`
6. Note the Distribution ID

## Deployment

### Using the Deployment Script

1. Set environment variables:

```bash
export FRONTEND_S3_BUCKET=triggers-api-frontend
export CLOUDFRONT_DISTRIBUTION_ID=YOUR_DISTRIBUTION_ID
export REACT_APP_API_URL=https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod
export AWS_REGION=us-east-1
```

2. Run the deployment script:

```bash
cd frontend
./scripts/deploy.sh
```

### Manual Deployment

1. Build the frontend:

```bash
cd frontend
export REACT_APP_API_URL=https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod
npm run build
```

2. Upload to S3:

```bash
# Upload static assets with long cache
aws s3 sync dist/ s3://triggers-api-frontend/ \
    --region us-east-1 \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html" \
    --exclude "*.html"

# Upload HTML files with no cache
aws s3 sync dist/ s3://triggers-api-frontend/ \
    --region us-east-1 \
    --delete \
    --cache-control "no-cache, no-store, must-revalidate" \
    --include "*.html"
```

3. Invalidate CloudFront cache:

```bash
aws cloudfront create-invalidation \
    --distribution-id YOUR_DISTRIBUTION_ID \
    --paths "/*"
```

## Environment Variables

The frontend uses the following environment variable:

- `REACT_APP_API_URL`: API Gateway URL (set at build time)

**Important**: Environment variables must be set at build time, not runtime. They are baked into the JavaScript bundle during the build process.

## Troubleshooting

### CORS Issues

If you encounter CORS errors, verify that:
1. The backend API has CORS configured correctly
2. The API Gateway allows the CloudFront origin

### Routing Issues (404 on Refresh)

If you get 404 errors when refreshing pages:
1. Ensure CloudFront error pages are configured (403/404 → 200 → `/index.html`)
2. Or configure S3 website hosting error document to `index.html`

### API Connection Issues

If the frontend can't connect to the API:
1. Verify `REACT_APP_API_URL` is set correctly at build time
2. Check browser console for errors
3. Verify API Gateway is accessible
4. Check CORS configuration

## Testing Deployment

After deployment:

1. Visit your CloudFront URL
2. Test all features:
   - API key configuration
   - Send event
   - View inbox
   - View event details
   - Acknowledge/delete events
   - View statistics
3. Check browser console for errors
4. Test on mobile devices

## Updating Deployment

To update the deployment:

1. Make changes to the code
2. Run the deployment script again
3. The script will:
   - Build the new version
   - Upload to S3
   - Invalidate CloudFront cache

## Cost Considerations

- **S3**: Very low cost for static hosting
- **CloudFront**: Pay per request (first 1TB free per month)
- **Data Transfer**: Minimal for typical usage

## Security

- S3 bucket policy allows public read access (required for static hosting)
- API key is stored in browser localStorage (not secure for production - consider implementing proper authentication)
- All API calls use HTTPS
- CORS is configured on the backend

