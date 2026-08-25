#!/bin/bash
# UniSpot EC2 bootstrap script (Amazon Linux 2023)
# Installs the app, wires up environment variables from CloudFormation
# parameters, and runs it as a systemd service on port 80 behind SSM
# (no SSH key required — access instances via Session Manager instead).

set -euo pipefail

dnf update -y
dnf install -y python3.11 python3.11-pip git

APP_DIR=/opt/unispot
mkdir -p "$APP_DIR"

# --- In real deployment: replace this block with either
#     (a) `git clone <your-repo>` then `cp -r <repo>/app/* $APP_DIR`, or
#     (b) `aws s3 cp s3://<deployment-bucket>/unispot-app.zip .` and unzip.
# For this bootstrap we assume the app code has been placed alongside this
# script (e.g. baked into a custom AMI, or pulled from a private S3 bucket
# holding the deployment artifact — never the public internet).
aws s3 cp "s3://${DEPLOYMENT_BUCKET}/unispot-app.zip" /tmp/unispot-app.zip
unzip -o /tmp/unispot-app.zip -d "$APP_DIR"

cd "$APP_DIR"
python3.11 -m pip install -r requirements.txt

cat > /etc/systemd/system/unispot.service <<EOF
[Unit]
Description=UniSpot Flask Application
After=network.target

[Service]
Environment=AWS_REGION=${AWS_REGION}
Environment=DYNAMODB_TABLE_NAME=${DYNAMODB_TABLE_NAME}
Environment=S3_BUCKET_NAME=${S3_BUCKET_NAME}
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/python3.11 -m gunicorn -w 2 -b 0.0.0.0:80 app:app
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable unispot
systemctl start unispot
