#!/bin/bash

# Frontend Deployment Script for S3 + CloudFront
# This script builds the frontend and deploys it to S3 + CloudFront

set -e

# Configuration
BUCKET_NAME="${FRONTEND_S3_BUCKET:-triggers-api-frontend-971422717446}"
CLOUDFRONT_DISTRIBUTION_ID="${CLOUDFRONT_DISTRIBUTION_ID:-E1392QCULSIX14}"
REGION="${AWS_REGION:-us-east-1}"
API_URL="${VITE_API_URL:-https://4g0xk0jne0.execute-api.us-east-1.amazonaws.com/prod/v1}"

echo "🚀 Starting frontend deployment..."
echo "   Bucket: $BUCKET_NAME"
echo "   Region: $REGION"
echo "   API URL: $API_URL"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Build the frontend
echo ""
echo "📦 Building frontend..."
export VITE_API_URL="$API_URL"
npm run build

if [ ! -d "dist" ]; then
    echo "❌ Build failed: dist directory not found"
    exit 1
fi

echo "✅ Build complete"

# Sync files to S3
echo ""
echo "📤 Uploading files to S3..."
aws s3 sync dist/ s3://$BUCKET_NAME/ \
    --region $REGION \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html" \
    --exclude "*.html"

# Upload HTML files with no cache
aws s3 sync dist/ s3://$BUCKET_NAME/ \
    --region $REGION \
    --delete \
    --cache-control "no-cache, no-store, must-revalidate" \
    --include "*.html"

echo "✅ Files uploaded to S3"

# Invalidate CloudFront cache if distribution ID is provided
if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo ""
    echo "🔄 Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
        --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
        --paths "/*" \
        --region $REGION > /dev/null
    echo "✅ CloudFront cache invalidation initiated"
else
    echo ""
    echo "⚠️  CLOUDFRONT_DISTRIBUTION_ID not set. Skipping cache invalidation."
    echo "   To invalidate cache, set CLOUDFRONT_DISTRIBUTION_ID environment variable"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Verify the deployment at your CloudFront URL"
echo "   2. Test all functionality"
echo "   3. Check browser console for any errors"

