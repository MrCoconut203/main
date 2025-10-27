#!/bin/bash
# ============================================================================
# Download YOLOv8 model from S3 before starting the application
# Set S3_MODEL_URI environment variable to use this feature
# Example: S3_MODEL_URI=s3://my-bucket/models/yolov8s.pt
# ============================================================================

set -e

echo "🚀 Starting AI Detection Service..."

# Check if S3_MODEL_URI is set and model doesn't exist locally
if [ ! -z "$S3_MODEL_URI" ] && [ ! -f "$MODEL_PATH" ]; then
    echo "📦 Downloading model from S3: $S3_MODEL_URI"
    
    # Install AWS CLI if not present (only in container startup)
    if ! command -v aws &> /dev/null; then
        echo "Installing AWS CLI..."
        pip install --quiet awscli
    fi
    
    # Download model from S3
    aws s3 cp "$S3_MODEL_URI" "$MODEL_PATH"
    echo "✅ Model downloaded successfully"
else
    if [ -f "$MODEL_PATH" ]; then
        echo "✅ Using existing model at $MODEL_PATH"
    else
        echo "⚠️  No model found. Please set S3_MODEL_URI or mount model at $MODEL_PATH"
    fi
fi

# Start the application with original start.sh
exec /start.sh
