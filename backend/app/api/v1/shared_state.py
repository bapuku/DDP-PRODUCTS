"""
Shared in-memory state for v3.0 human review queue.
Extracted to avoid cross-module import dependency between workflow.py and human_review.py.
"""
from typing import Any

pending_reviews: dict[str, dict[str, Any]] = {}
