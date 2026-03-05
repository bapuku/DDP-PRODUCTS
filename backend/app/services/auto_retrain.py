"""
Auto-retrain service — when regulatory DB changes (SVHC, sector_factors, thresholds),
optionally run ingest_and_train.py, compare metrics, hot-swap models if better.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()

# Backend root (backend/)
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
# Project root (eu-dpp-platform/) for running scripts
_PROJECT_ROOT = _BACKEND_ROOT.parent
_SCRIPTS_DIR = _PROJECT_ROOT / "scripts"
_INGEST_SCRIPT = _SCRIPTS_DIR / "ingest_and_train.py"
_MODELS_V3 = _PROJECT_ROOT / "data" / "models_v3"
_MODELS_V2 = _BACKEND_ROOT / "data" / "models_v2"
_RETRAIN_STATE_PATH = _BACKEND_ROOT / "data" / "retrain_state.json"

_retrain_status: dict[str, Any] = {
    "status": "idle",
    "last_run": None,
    "last_metrics": None,
    "last_error": None,
    "triggered_by": None,
}


def _load_retrain_state() -> dict[str, Any]:
    if not _RETRAIN_STATE_PATH.exists():
        return {}
    try:
        with open(_RETRAIN_STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_retrain_state(state: dict[str, Any]) -> None:
    _RETRAIN_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_RETRAIN_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _run_training_script() -> tuple[bool, dict[str, Any] | None, str | None]:
    """Run ingest_and_train.py; return (success, metrics_from_report, error_message)."""
    if not _INGEST_SCRIPT.exists():
        return False, None, f"Script not found: {_INGEST_SCRIPT}"
    try:
        proc = subprocess.run(
            ["python3", str(_INGEST_SCRIPT)],
            cwd=str(_PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=600,
            env={**__import__("os").environ, "EPOCHS": "50", "EARLY_STOP": "15"},
        )
        if proc.returncode != 0:
            return False, None, proc.stderr or proc.stdout or f"Exit code {proc.returncode}"
        report_path = _MODELS_V3 / "training_report.json"
        if not report_path.exists():
            return True, None, "Training report not found"
        with open(report_path, encoding="utf-8") as f:
            report = json.load(f)
        metrics = report.get("models", {})
        return True, metrics, None
    except subprocess.TimeoutExpired:
        return False, None, "Training timed out"
    except Exception as e:
        return False, None, str(e)


def _aggregate_metrics(metrics: dict[str, Any]) -> float:
    """Single score for comparison: mean of F1 (classifiers) and R² (regressors)."""
    if not metrics:
        return 0.0
    scores = []
    for v in metrics.values():
        if isinstance(v, dict):
            if "f1" in v:
                scores.append(v["f1"])
            elif "cv_f1" in v:
                scores.append(v["cv_f1"])
            elif "r2" in v:
                scores.append(v["r2"])
            elif "cv_r2" in v:
                scores.append(v["cv_r2"])
    return sum(scores) / len(scores) if scores else 0.0


def _hot_swap_models() -> bool:
    """Copy models_v3/*.pkl to backend data/models_v2/ for inference."""
    if not _MODELS_V3.exists():
        return False
    _MODELS_V2.mkdir(parents=True, exist_ok=True)
    for pkl in _MODELS_V3.glob("*.pkl"):
        shutil.copy2(pkl, _MODELS_V2 / pkl.name)
    # Invalidate ml_inference cache so next request reloads
    try:
        from app.services import ml_inference
        if hasattr(ml_inference, "_models"):
            ml_inference._models.clear()
    except Exception as e:
        log.warning("auto_retrain_clear_cache_failed", error=str(e))
    return True


def trigger_retrain(changes: list[str]) -> None:
    """
    Called when regulatory watcher detects changes. Runs training in background
    (or synchronously for simplicity), compares metrics, hot-swaps if better.
    """
    global _retrain_status
    _retrain_status["status"] = "running"
    _retrain_status["triggered_by"] = changes
    _retrain_status["last_run"] = datetime.now(timezone.utc).isoformat()
    _retrain_status["last_error"] = None

    try:
        ok, new_metrics, err = _run_training_script()
        if not ok:
            _retrain_status["status"] = "error"
            _retrain_status["last_error"] = err
            log.warning("auto_retrain_failed", error=err)
            _save_retrain_state({"last_error": err, "last_run": _retrain_status["last_run"]})
            return

        prev_state = _load_retrain_state()
        prev_score = prev_state.get("aggregate_score")
        new_score = _aggregate_metrics(new_metrics) if new_metrics else 0.0

        if prev_score is None or new_score >= prev_score:
            if _hot_swap_models():
                _retrain_status["status"] = "completed"
                _retrain_status["last_metrics"] = new_metrics
                _save_retrain_state({
                    "aggregate_score": new_score,
                    "last_metrics": new_metrics,
                    "last_run": _retrain_status["last_run"],
                    "hot_swapped": True,
                })
                log.info("auto_retrain_hot_swap", score=new_score, metrics=new_metrics)
            else:
                _retrain_status["status"] = "completed"
                _retrain_status["last_error"] = "Hot-swap copy failed"
        else:
            _retrain_status["status"] = "completed_no_swap"
            _retrain_status["last_metrics"] = new_metrics
            _retrain_status["last_error"] = f"New score {new_score:.4f} < previous {prev_score:.4f}; keeping old models"
            _save_retrain_state({
                "aggregate_score": prev_score,
                "last_run": _retrain_status["last_run"],
                "hot_swapped": False,
                "rejected_score": new_score,
            })
            log.warning("auto_retrain_rejected", new_score=new_score, prev_score=prev_score)
    except Exception as e:
        _retrain_status["status"] = "error"
        _retrain_status["last_error"] = str(e)
        log.exception("auto_retrain_error", error=str(e))


def get_retrain_status() -> dict[str, Any]:
    """Return current retrain status for API."""
    state = _load_retrain_state()
    return {
        "status": _retrain_status.get("status", "idle"),
        "last_run": _retrain_status.get("last_run"),
        "last_metrics": _retrain_status.get("last_metrics") or state.get("last_metrics"),
        "last_error": _retrain_status.get("last_error"),
        "triggered_by": _retrain_status.get("triggered_by"),
        "aggregate_score": state.get("aggregate_score"),
        "hot_swapped_last": state.get("hot_swapped"),
    }
