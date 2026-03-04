#!/bin/bash
# ================================================================
#  EU DPP Platform — Script unifié : clés API + deploy VPS
#  Exécuter : bash scripts/setup-and-deploy.sh
# ================================================================

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VPS_HOST="root@51.77.144.54"
VPS_PATH="/opt/dpp-platform"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  EU DPP Platform — Setup complet + Déploiement production   ║"
echo "║  VPS: 51.77.144.54 · SovereignPiAlpha France Ltd            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ──────────────────────────────────────────────────────────────────
# 1. COLLECTE DES CLÉS API
# ──────────────────────────────────────────────────────────────────

echo "━━━ ÉTAPE 1/5 — Clés API LLM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "  ANTHROPIC (Claude Sonnet 4 / Opus 4)"
echo "  → https://console.anthropic.com/settings/keys"
read -rp "  ANTHROPIC_API_KEY : " ANTHROPIC_KEY
echo ""

echo "  OPENAI (GPT-4o + Embeddings)"
echo "  → https://platform.openai.com/api-keys"
read -rp "  OPENAI_API_KEY : " OPENAI_KEY
echo ""

echo "  HUGGING FACE (Mistral, Llama, open source)"
echo "  → https://huggingface.co/settings/tokens"
read -rp "  HUGGINGFACE_API_KEY : " HF_KEY
echo ""

# ──────────────────────────────────────────────────────────────────
# 2. ÉCRITURE .ENV LOCAL
# ──────────────────────────────────────────────────────────────────

echo "━━━ ÉTAPE 2/5 — Configuration locale ━━━━━━━━━━━━━━━━━━━━━━━━"

# backend/.env
cat > "$ROOT/backend/.env" << EOF
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
ANTHROPIC_MODEL=claude-sonnet-4-20250514
OPENAI_API_KEY=${OPENAI_KEY}
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
HUGGINGFACE_API_KEY=${HF_KEY}
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
EOF
echo "  ✅ backend/.env"

# infrastructure/.env — conserver les clés existantes (DB, Kafka...) et ajouter/remplacer LLM
INFRA_ENV="$ROOT/infrastructure/.env"
if [ -f "$INFRA_ENV" ]; then
  grep -v "ANTHROPIC_API_KEY\|OPENAI_API_KEY\|HUGGINGFACE_API_KEY\|ANTHROPIC_MODEL\|OPENAI_MODEL\|OPENAI_EMBEDDING_MODEL\|HF_MODEL" "$INFRA_ENV" > "${INFRA_ENV}.tmp" 2>/dev/null || true
  mv "${INFRA_ENV}.tmp" "$INFRA_ENV"
fi
cat >> "$INFRA_ENV" << EOF
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
ANTHROPIC_MODEL=claude-sonnet-4-20250514
OPENAI_API_KEY=${OPENAI_KEY}
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
HUGGINGFACE_API_KEY=${HF_KEY}
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
EOF
echo "  ✅ infrastructure/.env"

# ──────────────────────────────────────────────────────────────────
# 3. GIT COMMIT + PUSH (code seulement, pas les .env)
# ──────────────────────────────────────────────────────────────────

echo ""
echo "━━━ ÉTAPE 3/5 — Git push ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$ROOT"
# S'assurer que .env est dans .gitignore
grep -qxF '*.env' .gitignore 2>/dev/null || echo '*.env' >> .gitignore
grep -qxF 'backend/.env' .gitignore 2>/dev/null || echo 'backend/.env' >> .gitignore
grep -qxF 'infrastructure/.env' .gitignore 2>/dev/null || echo 'infrastructure/.env' >> .gitignore

if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m "chore: update scripts and gitignore for API key setup" 2>/dev/null || true
  git push origin main 2>&1 | tail -3
  echo "  ✅ Code pushé"
else
  echo "  ✅ Rien à pusher (code à jour)"
fi

# ──────────────────────────────────────────────────────────────────
# 4. DÉPLOIEMENT VPS
# ──────────────────────────────────────────────────────────────────

echo ""
echo "━━━ ÉTAPE 4/5 — Déploiement VPS 51.77.144.54 ━━━━━━━━━━━━━━━━"
echo ""

ssh -o StrictHostKeyChecking=no "$VPS_HOST" << REMOTESCRIPT
set -e
cd ${VPS_PATH}

echo "  → Git pull..."
git pull origin main 2>&1 | tail -2

echo "  → Injection des clés API..."
cd infrastructure
grep -v "ANTHROPIC_API_KEY\|OPENAI_API_KEY\|HUGGINGFACE_API_KEY\|ANTHROPIC_MODEL\|OPENAI_MODEL\|OPENAI_EMBEDDING_MODEL\|HF_MODEL" .env > .env.tmp 2>/dev/null || true
mv .env.tmp .env 2>/dev/null || true
cat >> .env << 'ENVBLOCK'
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
ANTHROPIC_MODEL=claude-sonnet-4-20250514
OPENAI_API_KEY=${OPENAI_KEY}
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
HUGGINGFACE_API_KEY=${HF_KEY}
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
ENVBLOCK
echo "  ✅ Clés injectées"

echo "  → Build API..."
docker compose build --no-cache dpp-api 2>&1 | tail -3
docker compose up -d --no-deps --force-recreate dpp-api
echo "  ✅ API redémarrée"

echo "  → Build Frontend..."
docker compose -f docker-compose.prod.yml build --no-cache dpp-frontend 2>&1 | tail -3
docker compose -f docker-compose.prod.yml up -d --no-deps --force-recreate dpp-frontend
echo "  ✅ Frontend redémarré"

echo "  → Attente démarrage (20s)..."
sleep 20
REMOTESCRIPT

# ──────────────────────────────────────────────────────────────────
# 5. VÉRIFICATION
# ──────────────────────────────────────────────────────────────────

echo ""
echo "━━━ ÉTAPE 5/5 — Vérification ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ssh -o StrictHostKeyChecking=no "$VPS_HOST" << 'VERIFY'
echo "  ─── Health ───"
curl -s http://localhost:8100/health
echo ""

echo "  ─── LLM Providers ───"
curl -s http://localhost:8100/api/v1/agents/providers | python3 -c '
import sys, json
try:
    providers = json.load(sys.stdin)
    for p in providers:
        s = "✅ CONNECTÉ" if p["configured"] else "❌ NON CONFIGURÉ"
        print(f"  {p[\"name\"]:30s} {s}  ({p[\"default_model\"]})")
except:
    print("  ⚠️  API pas encore prête, réessayez dans 30s")
'

echo ""
echo "  ─── Services Docker ───"
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep dpp

echo ""
echo "  ─── Pages Frontend ───"
for p in / /agents /connectors /blockchain /qr /dpp /reports /landing; do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8110$p)
  echo "  $p → $code"
done

echo ""
echo "  ─── Test Assistant IA ───"
curl -s -X POST http://localhost:8110/api/v1/assistant/chat \
  -H 'Content-Type: application/json' \
  -H 'Accept-Language: fr' \
  -d '{"message":"Quels providers LLM sont connectés?"}' | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
    resp = d.get("response","")
    print(f"  Assistant: {resp[:200]}...")
except:
    print("  ⚠️  Assistant pas encore disponible")
'
VERIFY

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ DÉPLOIEMENT COMPLET                                     ║"
echo "║                                                              ║"
echo "║  Plateforme : http://51.77.144.54:8110/                      ║"
echo "║  Landing    : http://51.77.144.54:8110/landing                ║"
echo "║  API Docs   : http://51.77.144.54:8110/docs                  ║"
echo "║  Providers  : http://51.77.144.54:8110/api/v1/agents/providers║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
