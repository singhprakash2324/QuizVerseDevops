#!/usr/bin/env bash
# ==============================================================================
# EC2 Setup Script for QuizVerse Stack (Ubuntu 22.04 / 24.04 LTS)
# Installs Docker, Docker Compose V2, configures user permissions, and verifies versions.
# ==============================================================================

set -euo pipefail

echo "==> Updating package indices and upgrading existing packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

echo "==> Installing prerequisites..."
sudo apt-get install -y ca-certificates curl gnupg lsb-release

echo "==> Installing Docker and Docker Compose plugin..."
sudo apt-get install -y docker.io docker-compose-v2

echo "==> Ensuring Docker daemon is enabled and started..."
sudo systemctl enable docker
sudo systemctl start docker

echo "==> Adding 'ubuntu' user to docker group..."
sudo usermod -aG docker ubuntu || true

echo "==> Verifying installations:"
docker --version
docker compose version

echo "=============================================================================="
echo "Setup complete! Please log out and back in (or run 'newgrp docker') to apply"
echo "docker group permissions without sudo."
echo "=============================================================================="
