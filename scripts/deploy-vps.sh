#!/bin/bash
# EU DPP Platform - VPS OVH Deployment Script
# Target: Ubuntu 25.04, vps-d6ab33ba.vps.ovh.net (51.77.144.54)
# Usage: ssh root@51.77.144.54 'bash -s' < scripts/deploy-vps.sh

set -euo pipefail

VPS_IP="51.77.144.54"
REPO="https://github.com/bapuku/DDP-PRODUCTS.git"
APP_DIR="/opt/dpp-platform"

echo "========================================="
echo "EU DPP Platform - VPS Deployment"
echo "Target: $VPS_IP (Ubuntu 25.04)"
echo "========================================="

# 1. System update
echo "[1/7] Updating system..."
apt-get update -qq && apt-get upgrade -y -qq

# 2. Install Docker
echo "[2/7] Installing Docker..."
if ! command -v docker &> /dev/null; then
    apt-get install -y -qq ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    echo "Docker installed."
else
    echo "Docker already installed."
fi

# 3. Install Docker Compose plugin (v2)
echo "[3/7] Verifying Docker Compose..."
docker compose version || {
    apt-get install -y -qq docker-compose-plugin
}

# 4. Clone/pull repository
echo "[4/7] Cloning repository..."
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull origin main
else
    git clone "$REPO" "$APP_DIR"
    cd "$APP_DIR"
fi

# 5. Create production .env if not exists
echo "[5/7] Setting up environment..."
if [ ! -f "$APP_DIR/infrastructure/.env" ]; then
    cp "$APP_DIR/infrastructure/.env.production" "$APP_DIR/infrastructure/.env"
    # Generate random passwords
    RANDOM_PG_PASS=$(openssl rand -base64 24 | tr -d '=/+' | head -c 24)
    RANDOM_NEO4J_PASS=$(openssl rand -base64 24 | tr -d '=/+' | head -c 24)
    RANDOM_SECRET=$(openssl rand -base64 32 | tr -d '=/+' | head -c 32)
    sed -i "s/dpp-prod-change-me/$RANDOM_PG_PASS/g" "$APP_DIR/infrastructure/.env"
    sed -i "s/neo4j\/dpp-prod-change-me/neo4j\/$RANDOM_NEO4J_PASS/g" "$APP_DIR/infrastructure/.env"
    sed -i "s/change-me-to-a-random-32-char-string/$RANDOM_SECRET/g" "$APP_DIR/infrastructure/.env"
    echo "Production .env created with random passwords."
    echo "IMPORTANT: Save these credentials!"
    echo "  PostgreSQL: dpp / $RANDOM_PG_PASS"
    echo "  Neo4j: neo4j / $RANDOM_NEO4J_PASS"
    echo "  Secret key: $RANDOM_SECRET"
else
    echo "Using existing .env file."
fi

# 6. Open firewall ports
echo "[6/7] Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8000/tcp
    ufw allow 3000/tcp
    ufw --force enable
    echo "Firewall configured."
else
    echo "ufw not found, skipping firewall."
fi

# 7. Build and start
echo "[7/7] Building and starting services..."
cd "$APP_DIR/infrastructure"
docker compose -f docker-compose.prod.yml --env-file .env build --no-cache
docker compose -f docker-compose.prod.yml --env-file .env up -d

echo ""
echo "========================================="
echo "Deployment complete!"
echo "========================================="
echo ""
echo "Services:"
echo "  Frontend:  http://$VPS_IP"
echo "  API:       http://$VPS_IP:8000"
echo "  API Docs:  http://$VPS_IP/docs"
echo "  Health:    http://$VPS_IP/health"
echo ""
echo "Management:"
echo "  Logs:    cd $APP_DIR/infrastructure && docker compose -f docker-compose.prod.yml logs -f"
echo "  Status:  docker compose -f docker-compose.prod.yml ps"
echo "  Stop:    docker compose -f docker-compose.prod.yml down"
echo "  Restart: docker compose -f docker-compose.prod.yml restart"
echo ""
