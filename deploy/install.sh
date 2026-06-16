#!/bin/bash
# ==============================================================================
# Installation and deployment script for the Load Balanced FastAPI application.
# Runs on the EC2 instance to configure the runtime, pull the artifact from S3,
# and setup the systemd service.
# ==============================================================================

set -euo pipefail

# Configurable S3 Bucket Name - can be passed as the first parameter or environment variable
S3_BUCKET="${1:-your-s3-bucket-name}"
DEPLOY_DIR="/opt/load-balanced-app"
ARTIFACT_NAME="load-balanced-app.zip"

echo "=== Starting deployment setup ==="

# 1. Remove standard HTTP servers (Apache httpd/Nginx) if present
echo "Removing any conflicting HTTP servers..."
if systemctl list-unit-files | grep -q httpd; then
    echo "Stopping and disabling httpd..."
    systemctl stop httpd || true
    systemctl disable httpd || true
fi
if systemctl list-unit-files | grep -q nginx; then
    echo "Stopping and disabling nginx..."
    systemctl stop nginx || true
    systemctl disable nginx || true
fi

# Detect package manager (dnf is default on AL2023, yum on AL2)
PKG_MANAGER="dnf"
if ! command -v dnf &> /dev/null; then
    PKG_MANAGER="yum"
fi

echo "Using package manager: ${PKG_MANAGER}"
${PKG_MANAGER} remove -y httpd nginx || true
${PKG_MANAGER} install -y python3 python3-pip unzip


# 2. Setup target deployment directories
echo "Creating deployment directory at ${DEPLOY_DIR}..."
mkdir -p "${DEPLOY_DIR}"
chown -R ec2-user:ec2-user "${DEPLOY_DIR}"

# 3. Download the artifact from S3 using AWS CLI
echo "Downloading application artifact from S3 bucket: s3://${S3_BUCKET}..."
# The instance needs an IAM Role with AmazonS3ReadOnlyAccess policy attached
aws s3 cp "s3://${S3_BUCKET}/${ARTIFACT_NAME}" "${DEPLOY_DIR}/${ARTIFACT_NAME}"

# 4. Extract package contents
echo "Extracting artifact archive..."
unzip -o "${DEPLOY_DIR}/${ARTIFACT_NAME}" -d "${DEPLOY_DIR}"
chown -R ec2-user:ec2-user "${DEPLOY_DIR}"

# 5. Create Python Virtual Environment and install dependencies
echo "Setting up Python virtual environment..."
python3 -m venv "${DEPLOY_DIR}/.venv"
"${DEPLOY_DIR}/.venv/bin/pip" install --upgrade pip
"${DEPLOY_DIR}/.venv/bin/pip" install -r "${DEPLOY_DIR}/requirements.txt"

# 6. Configure and start Systemd Service
echo "Configuring systemd service..."
cp "${DEPLOY_DIR}/deploy/app.service" /etc/systemd/system/app.service
systemctl daemon-reload
systemctl enable app.service
systemctl restart app.service

echo "=== Deployment setup completed successfully ==="
