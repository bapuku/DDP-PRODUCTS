"""
Centralized regulatory database — single source of truth for calendar, frameworks,
SVHC list, RoHS exemptions, sector factors, carbon classes.
Data is loaded from backend/data/regulations.json and can be updated by the regulatory watcher.
"""
from pathlib import Path
from typing import Any
import json
from datetime import datetime, timezone

_REGULATIONS: dict[str, Any] | None = None
_REGULATIONS_PATH: Path = (
    Path(__file__).resolve().parent.parent.parent / "data" / "regulations.json"
)


def _ensure_loaded() -> dict[str, Any]:
    global _REGULATIONS
    if _REGULATIONS is None:
        if not _REGULATIONS_PATH.exists():
            raise FileNotFoundError(f"Regulations file not found: {_REGULATIONS_PATH}")
        with open(_REGULATIONS_PATH, encoding="utf-8") as f:
            _REGULATIONS = json.load(f)
    return _REGULATIONS


def load_regulations() -> dict[str, Any]:
    """Load regulations from JSON (idempotent; reloads from disk)."""
    global _REGULATIONS
    if not _REGULATIONS_PATH.exists():
        raise FileNotFoundError(f"Regulations file not found: {_REGULATIONS_PATH}")
    with open(_REGULATIONS_PATH, encoding="utf-8") as f:
        _REGULATIONS = json.load(f)
    return _REGULATIONS


def get_version() -> dict[str, str]:
    """Return current version number and updated_at."""
    data = _ensure_loaded()
    return dict(data.get("version", {"number": "0.0.0", "updated_at": ""}))


def get_changelog() -> list[dict[str, Any]]:
    """Return changelog entries (version, date, changes)."""
    data = _ensure_loaded()
    return list(data.get("changelog", []))


def get_calendar(locale: str = "en") -> list[dict[str, Any]]:
    """Return regulatory calendar for locale (en/fr)."""
    data = _ensure_loaded()
    cal = data.get("calendar") or {}
    if locale not in ("en", "fr"):
        locale = "en"
    return list(cal.get(locale, cal.get("en", [])))


def get_frameworks(locale: str = "en") -> list[str]:
    """Return list of supported frameworks for locale."""
    data = _ensure_loaded()
    fw = data.get("frameworks") or {}
    if locale not in ("en", "fr"):
        locale = "en"
    return list(fw.get(locale, fw.get("en", [])))


def get_svhc_list() -> list[dict[str, Any]]:
    """Return REACH SVHC candidate list (name, cas, ec, reason)."""
    data = _ensure_loaded()
    return list(data.get("svhc_list", []))


def get_svhc_known() -> dict[str, dict[str, Any]]:
    """Return known SVHC by CAS for SCIP lookup (cas -> {name, threshold_pct, status})."""
    data = _ensure_loaded()
    return dict(data.get("svhc_known", {}))


def get_rohs_exemptions() -> dict[str, dict[str, Any]]:
    """Return RoHS exemption codes (code -> {description, status, expiry, applicable_categories})."""
    data = _ensure_loaded()
    return dict(data.get("rohs_exemptions", {}))


def get_sector_factors() -> dict[str, dict[str, float]]:
    """Return impact factors per sector (sector -> {co2_per_kg, water_per_kg, ...})."""
    data = _ensure_loaded()
    return dict(data.get("sector_factors", {}))


def get_carbon_classes() -> list[tuple[str, float, float]]:
    """Return carbon classes as (class_letter, min_co2, max_co2). Last max is inf."""
    data = _ensure_loaded()
    raw = data.get("carbon_classes", [
        ["A", 0, 20], ["B", 20, 40], ["C", 40, 60], ["D", 60, 80],
        ["E", 80, 100], ["F", 100, 150], ["G", 150, float("inf")],
    ])
    out = []
    for i, row in enumerate(raw):
        cls, lo, hi = row[0], float(row[1]), float(row[2])
        if i == len(raw) - 1 and hi > 1e30:
            hi = float("inf")
        out.append((cls, lo, hi))
    return out


def _bump_version_and_save(data: dict[str, Any], change_descriptions: list[str]) -> None:
    """Increment version, append changelog, persist."""
    global _REGULATIONS
    ver = data.get("version", {})
    num = ver.get("number", "0.0.0")
    parts = num.split(".")
    if len(parts) == 3:
        try:
            parts[-1] = str(int(parts[-1]) + 1)
            num = ".".join(parts)
        except ValueError:
            num = f"{num}.1"
    else:
        num = "1.0.0"
    data["version"] = {
        "number": num,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    changelog = data.get("changelog", [])
    changelog.insert(0, {
        "version": num,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "changes": change_descriptions or ["Regulatory update"],
    })
    data["changelog"] = changelog[:50]
    _REGULATIONS = data
    with open(_REGULATIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_regulation(key: str, value: Any) -> None:
    """
    Update a top-level key in the regulations DB, increment version, and persist.
    Used by the regulatory watcher after detecting changes.
    """
    data = _ensure_loaded()
    data[key] = value
    _bump_version_and_save(data, [f"Updated {key} via regulatory watcher"])


def update_regulations_batch(updates: dict[str, Any], change_descriptions: list[str]) -> None:
    """Update multiple top-level keys at once, increment version once, and persist."""
    global _REGULATIONS
    data = _ensure_loaded()
    for key, value in updates.items():
        data[key] = value
    _bump_version_and_save(data, change_descriptions)
