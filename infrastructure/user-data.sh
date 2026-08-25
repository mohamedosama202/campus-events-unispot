#!/bin/bash
# UniSpot EC2 bootstrap script (Amazon Linux 2023)
# Installs the app, wires up environment variables from CloudFormation
# parameters, and runs it as a systemd service on port 80 behind SSM
# (no SSH key required — access instances via Session Manager instead).

set -euo pipefail

dnf update -y
dnf install -y python3.11 python3.11-pip git unzip

APP_DIR=/opt/unispot
mkdir -p "$APP_DIR"

# --- Pull deployment artifact from private S3 bucket ---
aws s3 cp "s3://${DEPLOYMENT_BUCKET}/unispot-app.zip" /tmp/unispot-app.zip
unzip -o /tmp/unispot-app.zip -d "$APP_DIR"

cd "$APP_DIR"
python3.11 -m pip install -r requirements.txt

# --- Create dedicated app user (security best practice) ---
useradd --system --no-create-home unispot || true
chown -R unispot:unispot "$APP_DIR"

cat > /etc/systemd/system/unispot.service <<EOF
[Unit]
Description=UniSpot Flask Application
After=network.target

[Service]
Environment=AWS_REGION=eu-north-1
Environment=DYNAMODB_TABLE_NAME=UniSpotEvents
Environment=S3_BUCKET_NAME=unispot-event-images-490497823432
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/python3.11 -m gunicorn -w 2 -b 0.0.0.0:80 app:app
Restart=always
RestartSec=5
User=unispot
Group=unispot

[Install]
WantedBy=multi-user.target
EOF

# --- Allow non-root user to bind port 80 ---
setcap 'cap_net_bind_service=+ep' /usr/bin/python3.11

systemctl daemon-reload
systemctl enable unispot
systemctl start unispot
