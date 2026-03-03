"""
Backend i18n: Accept-Language + centralized FR/EN messages for errors, calendar, status.
"""
from typing import Any

from fastapi import Request, Depends

LOCALES = ("en", "fr")
DEFAULT_LOCALE = "en"

# Keys: error messages, compliance calendar descriptions, framework names, workflow messages.
MESSAGES: dict[str, dict[str, Any]] = {
    "en": {
        "errors": {
            "dpp_not_found": "DPP not found",
            "product_not_found": "Product not found",
            "passport_not_found": "Passport not found",
            "invalid_credentials": "Invalid credentials",
            "duplicate_serial_gtin": "Duplicate serial number or GTIN",
            "workflow_error": "Workflow error: {detail}",
            "thread_not_found": "Thread not found or already processed",
            "compliance_check_failed": "Compliance check failed: {detail}",
            "internal_error": "An internal error occurred.",
            "too_many_requests": "Too many requests",
        },
        "calendar": [
            {"year": 2025, "regulation": "ESPR", "deadline": "2025-08-18", "description": "ESPR delegated acts adoption"},
            {"year": 2026, "regulation": "Battery Reg", "deadline": "2026-02-18", "description": "Battery passport mandatory (LMT, EV)"},
            {"year": 2027, "regulation": "ESPR", "deadline": "2027-01-01", "description": "First product categories DPP"},
            {"year": 2027, "regulation": "Battery Reg", "deadline": "2027-08-18", "description": "Battery passport (industrial, SLI)"},
            {"year": 2030, "regulation": "Battery Reg", "deadline": "2030-12-31", "description": "Recycled content targets"},
            {"year": 2031, "regulation": "ESPR", "deadline": "2031-01-01", "description": "Extended product categories"},
            {"year": 2035, "regulation": "Battery Reg", "deadline": "2035-12-31", "description": "Stricter recycling targets"},
            {"year": 2036, "regulation": "ESPR", "deadline": "2036-01-01", "description": "Full DPP rollout target"},
        ],
        "frameworks": [
            "ESPR",
            "Battery Regulation 2023/1542",
            "REACH",
            "RoHS",
            "WEEE",
            "EU AI Act 2024/1689 (Arts. 12-14)",
        ],
    },
    "fr": {
        "errors": {
            "dpp_not_found": "DPP introuvable",
            "product_not_found": "Produit introuvable",
            "passport_not_found": "Passeport introuvable",
            "invalid_credentials": "Identifiants invalides",
            "duplicate_serial_gtin": "Numéro de série ou GTIN en double",
            "workflow_error": "Erreur de workflow : {detail}",
            "thread_not_found": "Thread introuvable ou déjà traité",
            "compliance_check_failed": "Échec du contrôle de conformité : {detail}",
            "internal_error": "Une erreur interne s'est produite.",
            "too_many_requests": "Trop de requêtes",
        },
        "calendar": [
            {"year": 2025, "regulation": "ESPR", "deadline": "2025-08-18", "description": "Adoption des actes délégués ESPR"},
            {"year": 2026, "regulation": "Règlement Batteries", "deadline": "2026-02-18", "description": "Passeport batterie obligatoire (LMT, EV)"},
            {"year": 2027, "regulation": "ESPR", "deadline": "2027-01-01", "description": "Premières catégories de produits DPP"},
            {"year": 2027, "regulation": "Règlement Batteries", "deadline": "2027-08-18", "description": "Passeport batterie (industriel, SLI)"},
            {"year": 2030, "regulation": "Règlement Batteries", "deadline": "2030-12-31", "description": "Objectifs de contenu recyclé"},
            {"year": 2031, "regulation": "ESPR", "deadline": "2031-01-01", "description": "Catégories de produits étendues"},
            {"year": 2035, "regulation": "Règlement Batteries", "deadline": "2035-12-31", "description": "Objectifs de recyclage renforcés"},
            {"year": 2036, "regulation": "ESPR", "deadline": "2036-01-01", "description": "Déploiement complet DPP"},
        ],
        "frameworks": [
            "ESPR",
            "Règlement Batteries 2023/1542",
            "REACH",
            "RoHS",
            "DEEE",
            "EU AI Act 2024/1689 (Art. 12-14)",
        ],
    },
}


def get_locale_from_request(request: Request) -> str:
    """Read Accept-Language header; fallback to default."""
    raw = request.headers.get("accept-language") or ""
    for part in raw.split(","):
        lang = part.split(";")[0].strip()[:2].lower()
        if lang in LOCALES:
            return lang
    return DEFAULT_LOCALE


def t(key: str, locale: str, **params: Any) -> str:
    """Translate key for locale. Keys like 'errors.dpp_not_found'. Supports {placeholder} in values."""
    if locale not in MESSAGES:
        locale = DEFAULT_LOCALE
    msg = MESSAGES[locale]
    for part in key.split("."):
        msg = msg.get(part)
        if msg is None:
            # Fallback to English
            msg = MESSAGES[DEFAULT_LOCALE]
            for p in key.split("."):
                msg = msg.get(p)
                if msg is None:
                    return key
            break
    if isinstance(msg, str):
        return msg.format(**params) if params else msg
    return key


async def get_locale(request: Request) -> str:
    """FastAPI dependency: inject current locale from Accept-Language."""
    return get_locale_from_request(request)
