#!/bin/bash
# ================================================================
# EU DPP Platform — Déployer les clés API sur le VPS OVH
# Exécuter: bash scripts/deploy-keys-vps.sh
# ================================================================

set -e

VPS_HOST="root@51.77.144.54"
VPS_PATH="/opt/dpp-platform"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Déploiement des clés API sur VPS 51.77.144.54         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Lire les clés depuis le .env local
ENV_FILE="$(dirname "$0")/../infrastructure/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Fichier $ENV_FILE introuvable. Exécutez d'abord: bash scripts/setup-api-keys.sh"
  exit 1
fi

ANTHROPIC_KEY=$(grep "^ANTHROPIC_API_KEY=" "$ENV_FILE" | cut -d= -f2-)
OPENAI_KEY=$(grep "^OPENAI_API_KEY=" "$ENV_FILE" | cut -d= -f2-)
HF_KEY=$(grep "^HUGGINGFACE_API_KEY=" "$ENV_FILE" | cut -d= -f2-)

echo "Clés trouvées:"
echo "  Anthropic: ${ANTHROPIC_KEY:0:12}..."
echo "  OpenAI:    ${OPENAI_KEY:0:8}..."
echo "  HuggingFace: ${HF_KEY:0:8}..."
echo ""

# Injecter sur le VPS
echo ">>> Injection des clés sur le VPS..."
ssh -o StrictHostKeyChecking=no "$VPS_HOST" << REMOTE
cd ${VPS_PATH}/infrastructure

# Nettoyer les anciennes clés
grep -v "ANTHROPIC_API_KEY\|OPENAI_API_KEY\|HUGGINGFACE_API_KEY\|ANTHROPIC_MODEL\|OPENAI_MODEL\|OPENAI_EMBEDDING_MODEL\|HF_MODEL" .env > .env.tmp 2>/dev/null || true
mv .env.tmp .env 2>/dev/null || true

cat >> .env << 'ENVEOF'

# === LLM Providers ===
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
ANTHROPIC_MODEL=claude-sonnet-4-20250514
OPENAI_API_KEY=${OPENAI_KEY}
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
HUGGINGFACE_API_KEY=${HF_KEY}
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
ENVEOF

echo "✅ Clés injectées dans .env VPS"
REMOTE

echo ""
echo ">>> Pull du code + rebuild API..."
ssh -o StrictHostKeyChecking=no "$VPS_HOST" << 'REMOTE2'
cd /opt/dpp-platform
git pull origin main
cd infrastructure
docker compose build --no-cache dpp-api 2>&1 | tail -3
docker compose up -d --no-deps --force-recreate dpp-api
sleep 15
echo ""
echo ">>> Vérification des providers..."
curl -s http://localhost:8100/api/v1/agents/providers | python3 -c '
import sys, json
providers = json.load(sys.stdin)
for p in providers:
    status = "✅ CONNECTÉ" if p["configured"] else "❌ NON CONFIGURÉ"
    print(f"  {p[\"name']:30s} {status}  (modèle: {p[\"default_model\"]})")
'
echo ""
echo ">>> Health check..."
curl -s http://localhost:8100/health
echo ""
REMOTE2

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Déploiement terminé !                                 ║"
echo "║   API: http://51.77.144.54:8110/api/v1/agents/providers ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
