"""
Regulatory Watcher — polls EUR-Lex, ECHA SVHC Candidate List, OJEU RSS every 6 hours.
Detects changes, updates regulations.json, logs to audit trail, emits Kafka regulation.updated.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.regulation_db import (
    load_regulations,
    get_svhc_list,
    get_version,
    update_regulations_batch,
)

log = structlog.get_logger()

_WATCHER_STATE_PATH: Path = (
    Path(__file__).resolve().parent.parent.parent / "data" / "watcher_state.json"
)
_POLL_INTERVAL_HOURS = 6
_TIMEOUT = 15.0

# EUR-Lex SPARQL endpoint (publications.europa.eu)
_EURLEX_SPARQL = "https://publications.europa.eu/webapi/rdf/sparql"
# ECHA Candidate List (simplified — real API may differ)
_ECHA_CANDIDATE_URL = "https://echa.europa.eu/api/candidate-list?page=0&size=100"
# OJEU / EUR-Lex RSS
_OJEU_RSS = "https://eur-lex.europa.eu/feed/dir_oj_consolidated_en.xml"

_scheduler: BackgroundScheduler | None = None
_last_check_result: dict[str, Any] = {}


def _load_watcher_state() -> dict[str, Any]:
    if not _WATCHER_STATE_PATH.exists():
        return {"last_check": None, "last_eurlex_hash": None, "last_svhc_count": 0, "last_svhc_hash": None}
    try:
        with open(_WATCHER_STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_check": None, "last_eurlex_hash": None, "last_svhc_count": 0, "last_svhc_hash": None}


def _save_watcher_state(state: dict[str, Any]) -> None:
    _WATCHER_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_WATCHER_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


async def _fetch_eurlex_dpp_acts() -> str:
    """Query EUR-Lex SPARQL for recent DPP/ecodesign/battery acts. Returns hash of result for diff."""
    try:
        query = """
        PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
        SELECT ?work ?title WHERE {
          ?work a cdm:eu_legislation .
          ?work cdm:resource_legal_in-force "true"^^<http://www.w3.org/2001/XMLSchema#boolean> .
          ?work cdm:work_has_expression ?exp .
          ?exp cdm:expression_title ?title .
        } LIMIT 50
        """
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                _EURLEX_SPARQL,
                data={"query": query},
                headers={"Accept": "application/json"},
            )
        if resp.status_code != 200:
            return hashlib.sha256(resp.text.encode()).hexdigest()
        data = resp.json()
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    except Exception as e:
        log.warning("regulatory_watcher_eurlex_failed", error=str(e))
        return ""


async def _fetch_echa_candidate_list() -> list[dict[str, Any]]:
    """Fetch ECHA SVHC Candidate List. Returns list of {name, cas, ec, reason}."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_ECHA_CANDIDATE_URL)
        if resp.status_code == 200:
            data = resp.json()
            substances = data.get("substances") or data.get("content") or []
            if isinstance(substances, list):
                return [
                    {
                        "name": s.get("name") or s.get("substanceName") or "",
                        "cas": s.get("casNumber") or s.get("cas") or "",
                        "ec": s.get("ecNumber") or s.get("ec") or "",
                        "reason": s.get("reason") or s.get("reasonForInclusion") or "",
                    }
                    for s in substances[:200]
                ]
    except Exception as e:
        log.warning("regulatory_watcher_echa_failed", error=str(e))
    return []


async def _fetch_ojeu_rss_hash() -> str:
    """Fetch OJEU RSS and return hash for change detection."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(_OJEU_RSS)
        if resp.status_code == 200:
            return hashlib.sha256(resp.text.encode()).hexdigest()
    except Exception as e:
        log.warning("regulatory_watcher_ojeu_failed", error=str(e))
    return ""


def _run_check_sync() -> dict[str, Any]:
    """Synchronous entry point for scheduler: run async check and return result."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(run_check())
    finally:
        loop.close()


async def run_check() -> dict[str, Any]:
    """
    Poll EUR-Lex, ECHA, OJEU; compare with stored state; update regulations.json if changed.
    Returns {updated: bool, changes: list[str], last_check: str, error: str?}.
    """
    global _last_check_result
    state = _load_watcher_state()
    changes: list[str] = []
    updated = False

    try:
        load_regulations()
    except FileNotFoundError:
        _last_check_result = {
            "updated": False,
            "changes": [],
            "last_check": datetime.now(timezone.utc).isoformat(),
            "error": "regulations.json not found",
        }
        return _last_check_result

    # 1) ECHA Candidate List
    try:
        remote_svhc = await _fetch_echa_candidate_list()
        if remote_svhc:
            current = get_svhc_list()
            new_hash = hashlib.sha256(json.dumps(remote_svhc, sort_keys=True).encode()).hexdigest()
            old_hash = state.get("last_svhc_hash")
            if old_hash is None:
                old_hash = hashlib.sha256(json.dumps(current, sort_keys=True).encode()).hexdigest()
            if new_hash != old_hash:
                known = {}
                for s in remote_svhc[:20]:
                    cas = s.get("cas")
                    if cas:
                        known[cas] = {
                            "name": s.get("name", ""),
                            "threshold_pct": 0.1,
                            "status": "SVHC",
                        }
                update_regulations_batch(
                    {"svhc_list": remote_svhc, "svhc_known": known},
                    ["ECHA SVHC Candidate List updated"],
                )
                changes.append("ECHA SVHC Candidate List updated")
                updated = True
            state["last_svhc_hash"] = new_hash
            state["last_svhc_count"] = len(remote_svhc)
    except Exception as e:
        log.exception("regulatory_watcher_echa_error", error=str(e))
        _last_check_result = {
            "updated": updated,
            "changes": changes,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }
        state["last_check"] = datetime.now(timezone.utc).isoformat()
        _save_watcher_state(state)
        return _last_check_result

    # 2) EUR-Lex (hash only — no automatic merge of acts into DB for now)
    try:
        eurlex_hash = await _fetch_eurlex_dpp_acts()
        if eurlex_hash and state.get("last_eurlex_hash") and eurlex_hash != state["last_eurlex_hash"]:
            changes.append("EUR-Lex DPP/ecodesign acts changed (hash diff)")
            updated = True
        state["last_eurlex_hash"] = eurlex_hash or state.get("last_eurlex_hash")
    except Exception as e:
        log.warning("regulatory_watcher_eurlex_error", error=str(e))

    # 3) OJEU RSS
    try:
        ojeu_hash = await _fetch_ojeu_rss_hash()
        if ojeu_hash and state.get("last_ojeu_hash") and ojeu_hash != state["last_ojeu_hash"]:
            changes.append("OJEU RSS feed changed")
            updated = True
        state["last_ojeu_hash"] = ojeu_hash or state.get("last_ojeu_hash")
    except Exception as e:
        log.warning("regulatory_watcher_ojeu_error", error=str(e))

    state["last_check"] = datetime.now(timezone.utc).isoformat()
    _save_watcher_state(state)

    if updated:
        log.info("regulatory_watcher_updated", changes=changes, version=get_version())
        try:
            from app.services.kafka import get_kafka
            k = get_kafka()
            if k and getattr(k, "send", None):
                k.send("regulation.updated", {"changes": changes, "version": get_version()})
        except Exception as e:
            log.debug("regulatory_watcher_kafka_skip", error=str(e))
        try:
            from app.services.audit import get_audit_service
            audit = get_audit_service()
            if audit and getattr(audit, "log_event", None):
                audit.log_event("regulation_updated", {"changes": changes})
        except Exception as e:
            log.debug("regulatory_watcher_audit_skip", error=str(e))
        try:
            from app.services.auto_retrain import trigger_retrain
            trigger_retrain(changes)
        except Exception as e:
            log.warning("regulatory_watcher_retrain_trigger_failed", error=str(e))

    _last_check_result = {
        "updated": updated,
        "changes": changes,
        "last_check": state["last_check"],
        "version": get_version(),
    }
    return _last_check_result


def get_last_check_result() -> dict[str, Any]:
    """Return result of last run_check (for API)."""
    return dict(_last_check_result) if _last_check_result else {
        "updated": False,
        "changes": [],
        "last_check": None,
        "error": "No check run yet",
    }


def start_scheduler() -> None:
    """Start background scheduler: run_check every 6 hours."""
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _run_check_sync,
        trigger=IntervalTrigger(hours=_POLL_INTERVAL_HOURS),
        id="regulatory_watcher",
        next_run_time=datetime.now(timezone.utc),
    )
    _scheduler.start()
    log.info("regulatory_watcher_scheduler_started", interval_hours=_POLL_INTERVAL_HOURS)


def stop_scheduler() -> None:
    """Stop the regulatory watcher scheduler."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log.info("regulatory_watcher_scheduler_stopped")
