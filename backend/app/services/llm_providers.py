"""
LLM Provider Service — unified access to Anthropic, OpenAI, Hugging Face models.
EU AI Act Art. 13: all LLM usage is transparent and logged.
"""
from typing import Any, Optional

import structlog

from app.config import settings

log = structlog.get_logger()

_providers_cache: dict[str, Any] = {}


def get_anthropic_llm(model: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 2000):
    """Get Anthropic Claude LLM (Sonnet 4 / Opus 4)."""
    key = f"anthropic:{model or settings.ANTHROPIC_MODEL}"
    if key not in _providers_cache:
        from langchain_anthropic import ChatAnthropic
        _providers_cache[key] = ChatAnthropic(
            model=model or settings.ANTHROPIC_MODEL,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        log.info("llm_provider_init", provider="anthropic", model=model or settings.ANTHROPIC_MODEL)
    return _providers_cache[key]


def get_openai_llm(model: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 2000):
    """Get OpenAI LLM (GPT-4o, GPT-4-turbo, etc.)."""
    key = f"openai:{model or settings.OPENAI_MODEL}"
    if key not in _providers_cache:
        from langchain_openai import ChatOpenAI
        _providers_cache[key] = ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        log.info("llm_provider_init", provider="openai", model=model or settings.OPENAI_MODEL)
    return _providers_cache[key]


def get_openai_embeddings(model: Optional[str] = None):
    """Get OpenAI embeddings model."""
    key = f"openai_embed:{model or settings.OPENAI_EMBEDDING_MODEL}"
    if key not in _providers_cache:
        from langchain_openai import OpenAIEmbeddings
        _providers_cache[key] = OpenAIEmbeddings(
            model=model or settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )
        log.info("embedding_provider_init", provider="openai", model=model or settings.OPENAI_EMBEDDING_MODEL)
    return _providers_cache[key]


def get_huggingface_llm(model: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 1000):
    """Get Hugging Face model via Inference API."""
    key = f"hf:{model or settings.HF_MODEL}"
    if key not in _providers_cache:
        from langchain_huggingface import HuggingFaceEndpoint
        _providers_cache[key] = HuggingFaceEndpoint(
            repo_id=model or settings.HF_MODEL,
            huggingfacehub_api_token=settings.HUGGINGFACE_API_KEY,
            temperature=temperature,
            max_new_tokens=max_tokens,
        )
        log.info("llm_provider_init", provider="huggingface", model=model or settings.HF_MODEL)
    return _providers_cache[key]


def get_huggingface_embeddings(model: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """Get Hugging Face sentence-transformers embeddings (runs locally)."""
    key = f"hf_embed:{model}"
    if key not in _providers_cache:
        from langchain_huggingface import HuggingFaceEmbeddings
        _providers_cache[key] = HuggingFaceEmbeddings(model_name=model)
        log.info("embedding_provider_init", provider="huggingface", model=model)
    return _providers_cache[key]


def get_best_available_llm(task: str = "general", temperature: float = 0.3, max_tokens: int = 2000):
    """
    Get the best available LLM based on configured API keys and task type.
    Priority: Anthropic (regulatory) > OpenAI (general) > HuggingFace (fallback).
    """
    if task in ("regulatory", "compliance", "legal") and settings.ANTHROPIC_API_KEY:
        return get_anthropic_llm(model="claude-sonnet-4-20250514", temperature=temperature, max_tokens=max_tokens), "anthropic"

    if settings.ANTHROPIC_API_KEY:
        return get_anthropic_llm(temperature=temperature, max_tokens=max_tokens), "anthropic"

    if settings.OPENAI_API_KEY:
        return get_openai_llm(temperature=temperature, max_tokens=max_tokens), "openai"

    if settings.HUGGINGFACE_API_KEY:
        return get_huggingface_llm(temperature=temperature, max_tokens=min(max_tokens, 1000)), "huggingface"

    raise RuntimeError("No LLM provider configured. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or HUGGINGFACE_API_KEY.")


def get_best_available_embeddings():
    """Get the best available embedding model. OpenAI > HuggingFace (local)."""
    if settings.OPENAI_API_KEY:
        return get_openai_embeddings(), "openai"
    return get_huggingface_embeddings(), "huggingface"


def list_available_providers() -> list[dict[str, Any]]:
    """List all configured LLM providers and their status."""
    providers = []

    providers.append({
        "id": "anthropic",
        "name": "Anthropic (Claude)",
        "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514"],
        "configured": bool(settings.ANTHROPIC_API_KEY),
        "default_model": settings.ANTHROPIC_MODEL,
        "use_case": "Regulatory analysis, compliance reasoning, agent orchestration",
        "priority": 1,
    })

    providers.append({
        "id": "openai",
        "name": "OpenAI (GPT)",
        "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "text-embedding-3-large"],
        "configured": bool(settings.OPENAI_API_KEY),
        "default_model": settings.OPENAI_MODEL,
        "use_case": "General reasoning, embeddings for vector search (GraphRAG)",
        "priority": 2,
    })

    providers.append({
        "id": "huggingface",
        "name": "Hugging Face",
        "models": [settings.HF_MODEL, "sentence-transformers/all-MiniLM-L6-v2"],
        "configured": bool(settings.HUGGINGFACE_API_KEY),
        "default_model": settings.HF_MODEL,
        "use_case": "Open-source models, local embeddings, cost-effective inference",
        "priority": 3,
    })

    return providers
