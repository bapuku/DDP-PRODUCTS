#!/usr/bin/env bash
# EU DPP Training Pipeline Runner v2.1
# Default: 200 epochs / EARLY_STOP=30 (best quality/cost ratio).
# Optional: SEAL_MODE=1 for iterative optimization after base training.
#
# Usage:
#   ./eu-dpp-platform/scripts/run_train_200_500.sh           # default 200ep
#   SEAL_MODE=1 ./eu-dpp-platform/scripts/run_train_200_500.sh  # 200ep + SEAL
#   EPOCHS=500 EARLY_STOP=50 ./eu-dpp-platform/scripts/run_train_200_500.sh  # custom

set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

export PYTHONUNBUFFERED=1
export DATA_PATH="${DATA_PATH:-$ROOT/DATASET/dpp_unified_sample_80k.csv}"

SCRIPT_PY="$ROOT/eu-dpp-platform/scripts/train_dpp_models_v2.py"

# Defaults (override via env vars)
: "${EPOCHS:=200}"
: "${EARLY_STOP:=30}"
: "${SEAL_MODE:=0}"

echo "=== EU DPP Training v2.1 ==="
echo "  EPOCHS=$EPOCHS | EARLY_STOP=$EARLY_STOP | SEAL_MODE=$SEAL_MODE"
echo ""

EPOCHS=$EPOCHS EARLY_STOP=$EARLY_STOP SEAL_MODE=$SEAL_MODE python3 "$SCRIPT_PY"
