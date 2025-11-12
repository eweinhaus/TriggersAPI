#!/bin/bash
# Build Lambda deployment package with correct architecture (x86_64)
# This script uses Docker to build a package compatible with AWS Lambda

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "📦 Building Lambda deployment package..."

# Clean previous builds
rm -rf .deploy lambda-deployment.zip

# Build using Docker with x86_64 platform
docker run --rm --platform linux/amd64 \
    -v "$PROJECT_ROOT:/var/task" \
    -w /var/task \
    public.ecr.aws/sam/build-python3.11:latest \
    bash -c "
        rm -rf .deploy && mkdir -p .deploy && 
        pip install --platform manylinux2014_x86_64 --only-binary=:all: --target .deploy -r requirements.txt && 
        cp -r src .deploy/ && 
        cd .deploy && 
        zip -r ../lambda-deployment.zip . -q && 
        echo '✅ Build complete' && 
        ls -lh ../lambda-deployment.zip
    "

echo "✅ Lambda package built: lambda-deployment.zip"
echo "   Size: $(ls -lh lambda-deployment.zip | awk '{print $5}')"


