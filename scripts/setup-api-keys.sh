#!/bin/bash
# ================================================================
# EU DPP Platform — Configuration des clés API LLM
# Exécuter: bash scripts/setup-api-keys.sh
# ================================================================

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   EU DPP Platform — Configuration des clés API LLM     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# --- Anthropic (Claude) ---
echo "1/3 — ANTHROPIC (Claude Sonnet 4 / Opus 4)"
echo "    Obtenir la clé: https://console.anthropic.com/settings/keys"
read -p "    ANTHROPIC_API_KEY: " ANTHROPIC_KEY
echo ""

# --- OpenAI (GPT-4o) ---
echo "2/3 — OPENAI (GPT-4o + Embeddings)"
echo "    Obtenir la clé: https://platform.openai.com/api-keys"
read -p "    OPENAI_API_KEY: " OPENAI_KEY
echo ""

# --- Hugging Face ---
echo "3/3 — HUGGING FACE (Mistral, Llama, modèles open source)"
echo "    Obtenir la clé: https://huggingface.co/settings/tokens"
read -p "    HUGGINGFACE_API_KEY: " HF_KEY
echo ""

# --- Écriture fichier .env local (backend) ---
ENV_BACKEND="$(dirname "$0")/../backend/.env"
cat > "$ENV_BACKEND" << EOF
# === LLM Providers (généré par setup-api-keys.sh) ===
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
ANTHROPIC_MODEL=claude-sonnet-4-20250514
OPENAI_API_KEY=${OPENAI_KEY}
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
HUGGINGFACE_API_KEY=${HF_KEY}
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
EOF
echo "✅ Backend .env écrit: $ENV_BACKEND"

# --- Écriture fichier .env infrastructure ---
ENV_INFRA="$(dirname "$0")/../infrastructure/.env"
if [ -f "$ENV_INFRA" ]; then
  # Supprimer les anciennes clés si elles existent
  grep -v "ANTHROPIC_API_KEY\|OPENAI_API_KEY\|HUGGINGFACE_API_KEY\|ANTHROPIC_MODEL\|OPENAI_MODEL\|OPENAI_EMBEDDING_MODEL\|HF_MODEL" "$ENV_INFRA" > "${ENV_INFRA}.tmp" || true
  mv "${ENV_INFRA}.tmp" "$ENV_INFRA"
fi
cat >> "$ENV_INFRA" << EOF

# === LLM Providers ===
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
ANTHROPIC_MODEL=claude-sonnet-4-20250514
OPENAI_API_KEY=${OPENAI_KEY}
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
HUGGINGFACE_API_KEY=${HF_KEY}
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
EOF
echo "✅ Infrastructure .env mis à jour: $ENV_INFRA"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Configuration terminée !                              ║"
echo "║                                                         ║"
echo "║   Pour déployer sur le VPS:                             ║"
echo "║   bash scripts/deploy-keys-vps.sh                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
