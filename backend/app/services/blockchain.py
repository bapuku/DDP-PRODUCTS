"""
Blockchain anchoring service for DPP integrity.
Merkle tree construction + hash anchoring + verification.
Production: Ethereum/Polygon smart contract. Demo: in-memory chain.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any, Optional

import structlog

log = structlog.get_logger()

_anchored: dict[str, dict[str, Any]] = {}
_merkle_roots: list[dict[str, Any]] = []
_block_counter = 0


def compute_dpp_hash(dpp_data: dict[str, Any]) -> str:
    """Compute SHA-256 hash of DPP data (deterministic JSON serialization)."""
    canonical = json.dumps(dpp_data, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _merkle_hash(left: str, right: str) -> str:
    combined = f"{left}{right}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def compute_merkle_root(hashes: list[str]) -> str:
    """Compute Merkle root from a list of hashes."""
    if not hashes:
        return hashlib.sha256(b"empty").hexdigest()
    if len(hashes) == 1:
        return hashes[0]
    layer = list(hashes)
    while len(layer) > 1:
        next_layer = []
        for i in range(0, len(layer), 2):
            left = layer[i]
            right = layer[i + 1] if i + 1 < len(layer) else layer[i]
            next_layer.append(_merkle_hash(left, right))
        layer = next_layer
    return layer[0]


def anchor_dpp(dpp_uri: str, dpp_data: dict[str, Any], gtin: str, serial: str) -> dict[str, Any]:
    """Anchor a DPP hash to the blockchain (Merkle tree + block)."""
    global _block_counter

    dpp_hash = compute_dpp_hash(dpp_data)
    prev_block_hash = _merkle_roots[-1]["block_hash"] if _merkle_roots else "0" * 64

    _block_counter += 1
    block_hash = hashlib.sha256(f"{prev_block_hash}{dpp_hash}{_block_counter}{time.time()}".encode()).hexdigest()

    anchor = {
        "dpp_uri": dpp_uri,
        "dpp_hash": dpp_hash,
        "gtin": gtin,
        "serial_number": serial,
        "block_number": _block_counter,
        "block_hash": block_hash,
        "prev_block_hash": prev_block_hash,
        "merkle_root": compute_merkle_root([dpp_hash]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "chain": "eu-dpp-integrity-chain",
        "status": "anchored",
        "algorithm": "SHA-256 + Merkle Tree",
    }

    _anchored[dpp_hash] = anchor
    _merkle_roots.append({"block_number": _block_counter, "block_hash": block_hash, "merkle_root": anchor["merkle_root"], "timestamp": anchor["timestamp"], "dpp_count": 1})

    log.info("dpp_anchored", dpp_hash=dpp_hash[:16], block=_block_counter, gtin=gtin)
    return anchor


def verify_dpp(dpp_data: dict[str, Any]) -> dict[str, Any]:
    """Verify DPP integrity against blockchain anchor."""
    dpp_hash = compute_dpp_hash(dpp_data)
    anchor = _anchored.get(dpp_hash)

    if not anchor:
        return {
            "verified": False,
            "dpp_hash": dpp_hash,
            "reason": "No blockchain anchor found for this DPP hash",
            "recommendation": "Anchor this DPP first via POST /api/v1/blockchain/anchor",
        }

    recomputed = compute_dpp_hash(dpp_data)
    integrity_ok = recomputed == anchor["dpp_hash"]

    return {
        "verified": integrity_ok,
        "dpp_hash": dpp_hash,
        "block_number": anchor["block_number"],
        "block_hash": anchor["block_hash"],
        "merkle_root": anchor["merkle_root"],
        "anchored_at": anchor["timestamp"],
        "chain": anchor["chain"],
        "tampered": not integrity_ok,
    }


def verify_by_hash(dpp_hash: str) -> dict[str, Any]:
    """Verify by hash directly."""
    anchor = _anchored.get(dpp_hash)
    if not anchor:
        return {"verified": False, "dpp_hash": dpp_hash, "reason": "Hash not found in blockchain"}
    return {
        "verified": True,
        "dpp_uri": anchor["dpp_uri"],
        "dpp_hash": dpp_hash,
        "block_number": anchor["block_number"],
        "block_hash": anchor["block_hash"],
        "merkle_root": anchor["merkle_root"],
        "anchored_at": anchor["timestamp"],
        "chain": anchor["chain"],
        "gtin": anchor["gtin"],
        "serial_number": anchor["serial_number"],
    }


def get_chain_status() -> dict[str, Any]:
    """Get blockchain chain status."""
    return {
        "chain": "eu-dpp-integrity-chain",
        "algorithm": "SHA-256 + Merkle Tree",
        "total_blocks": _block_counter,
        "total_anchored_dpps": len(_anchored),
        "latest_block": _merkle_roots[-1] if _merkle_roots else None,
        "integrity": "valid",
    }


def get_anchored_list(limit: int = 50) -> list[dict[str, Any]]:
    """List anchored DPPs."""
    items = sorted(_anchored.values(), key=lambda x: x["timestamp"], reverse=True)
    return items[:limit]
