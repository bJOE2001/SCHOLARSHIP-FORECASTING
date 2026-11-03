#!/usr/bin/env bash
# ==============================================================================
# Production Setup Script for DigitalOcean Droplet (Ubuntu 22.04 / 24.04 LTS)
# Deploys SCHOLARSHIP-FORECASTING as a native systemd service with Gunicorn/Uvicorn.
# ==============================================================================

set -euo pipefail

APP_DIR="/var/www/SCHOLARSHIP-FORECASTING"
SERVICE_NAME="scholarship-forecasting"

echo "==> 1. Updating APT packages & installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nginx curl git

echo "==> 2. Setting up application directory at ${APP_DIR}..."
sudo mkdir -p "${APP_DIR}"
sudo chown -R "$USER":"$USER" "${APP_DIR}"

# If running script from inside repo, copy files or assume current directory is target
if [ -f "app.py" ]; then
    echo "Copying repository files to ${APP_DIR}..."
    cp -r . "${APP_DIR}/"
fi

cd "${APP_DIR}"

echo "==> 3. Creating Python Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "==> 4. Installing Python dependencies..."
"${APP_DIR}/venv/bin/pip" install --upgrade pip setuptools wheel
"${APP_DIR}/venv/bin/pip" install -r requirements.txt

echo "==> 5. Ensuring models directory permissions..."
mkdir -p "${APP_DIR}/models"
sudo chown -R www-data:www-data "${APP_DIR}"
sudo chmod -R 775 "${APP_DIR}/models"

echo "==> 6. Installing Systemd Service..."
sudo cp "${APP_DIR}/deploy/scholarship-forecasting.service" "/etc/systemd/system/${SERVICE_NAME}.service"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

echo "==> 7. Verifying service status..."
sleep 2
if sudo systemctl is-active --quiet "${SERVICE_NAME}"; then
    echo "Service is ACTIVE and running on port 8000!"
    curl -s http://127.0.0.1:8000/health || true
    echo ""
else
    echo "Service failed to start. Showing logs:"
    sudo journalctl -u "${SERVICE_NAME}" -n 20 --no-pager
    exit 1
fi

echo "=========================================================================="
echo "Deployment successful!"
echo "Service is managed by systemd: sudo systemctl status ${SERVICE_NAME}"
echo "To view live logs: sudo journalctl -u ${SERVICE_NAME} -f"
echo "=========================================================================="
