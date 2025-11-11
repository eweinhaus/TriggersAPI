# Production Deployment Guide

## Deployment Status: ✅ Complete

**Deployment Date:** 2025-01-11  
**Status:** Frontend deployed to S3 + CloudFront

## Production URLs

### Frontend Dashboard
- **S3 Website URL:** http://triggers-api-frontend-971422717446.s3-website-us-east-1.amazonaws.com
- **CloudFront URL:** https://d1xoc8cf19dtpg.cloudfront.net
  - Status: Deploying (takes 5-15 minutes to fully propagate)
  - Use CloudFront URL for production (HTTPS, CDN, better performance)

### Backend API
- **API Gateway URL:** https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod
- **Health Check:** https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod/v1/health

## Infrastructure

### S3 Bucket
- **Name:** triggers-api-frontend-971422717446
- **Region:** us-east-1
- **Static Website Hosting:** Enabled
- **Public Access:** Configured (via CloudFront)

### CloudFront Distribution
- **Distribution ID:** E1392QCULSIX14
- **Domain:** d1xoc8cf19dtpg.cloudfront.net
- **Origin:** S3 bucket (triggers-api-frontend-971422717446)
- **HTTPS:** Enabled (redirects HTTP to HTTPS)
- **SPA Routing:** Configured (403/404 → 200 → /index.html)
- **Compression:** Enabled

## Usage

1. **Access the Dashboard:**
   - Navigate to: https://d1xoc8cf19dtpg.cloudfront.net
   - Or use S3 URL: http://triggers-api-frontend-971422717446.s3-website-us-east-1.amazonaws.com

2. **Configure API Key:**
   - Enter your API key in the header
   - For production, use API keys created in DynamoDB
   - For testing, use: `test-api-key-12345` (if using local mode)

3. **Use the Dashboard:**
   - Send events via the "Send Event" page
   - View inbox with pagination and filtering
   - View event details
   - View statistics with charts

## Updating Deployment

To update the frontend:

```bash
cd frontend
export VITE_API_URL=https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod
npm run build
aws s3 sync dist/ s3://triggers-api-frontend-971422717446/ \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "*.html"
aws s3 sync dist/ s3://triggers-api-frontend-971422717446/ \
    --delete \
    --cache-control "no-cache, no-store, must-revalidate" \
    --include "*.html"
aws cloudfront create-invalidation \
    --distribution-id E1392QCULSIX14 \
    --paths "/*"
```

## Troubleshooting

### CORS Issues
- Backend CORS is configured to allow all origins
- If issues persist, check API Gateway CORS settings

### CloudFront Not Working
- Wait 5-15 minutes for full deployment
- Check distribution status: `aws cloudfront get-distribution --id E1392QCULSIX14`
- Use S3 website URL as fallback

### API Connection Issues
- Verify API Gateway is accessible
- Check API key is valid
- Verify CORS headers in browser network tab

## Security Notes

- API keys are stored in browser localStorage (not secure for production)
- Consider implementing proper authentication for production use
- All API calls use HTTPS
- CloudFront provides DDoS protection and caching

## Cost Estimation

- **S3:** ~$0.023 per GB storage + $0.005 per 1,000 requests
- **CloudFront:** First 1TB free per month, then $0.085 per GB
- **API Gateway:** Pay per request
- **Lambda:** Pay per invocation
- **DynamoDB:** On-demand pricing

Typical usage: < $10/month for low to moderate traffic.

