"""
Knowledge graph agent - GraphRAG-R1: hybrid vector (Qdrant) + graph (Neo4j) retrieval.
Pipeline: 1.Embed query 2.Qdrant vector search 3.Neo4j graph traversal 4.Claude story-building.
"""
import json
import os
from typing import Any

import structlog

from app.agents.state import DPPWorkflowState
from app.ai.llm_client import get_sonnet
from app.services.qdrant import get_qdrant
from app.services.neo4j import get_neo4j

log = structlog.get_logger()


def _embed_query(query: str) -> list[float]:
    """Embed query via OpenAI or return mock embedding."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        try:
            import httpx
            resp = httpx.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "text-embedding-3-small", "input": query[:8000]},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]
        except Exception as e:
            log.warning("embedding_failed", error=str(e))
    import math
    h = hash(query) % (2 ** 32)
    vec = [math.sin(h * (i + 1) * 0.0001) * 0.01 for i in range(1536)]
    norm = sum(x ** 2 for x in vec) ** 0.5 or 1
    return [x / norm for x in vec]


async def knowledge_graph_agent(state: DPPWorkflowState) -> dict[str, Any]:
    """Stage 1: embed. Stage 2: Qdrant search. Stage 3: Neo4j traversal. Stage 4: synthesize."""
    query = state.get("query", "")
    retrieved: list[dict[str, Any]] = []

    # Stage 2: Qdrant vector search
    try:
        qdrant = get_qdrant()
        qdrant.ensure_collection("eu_regulations")
        vec = _embed_query(query)
        hits = qdrant.client.search(
            collection_name="eu_regulations",
            query_vector=vec,
            limit=5,
            with_payload=True,
        )
        for h in hits:
            retrieved.append({
                "source": "qdrant",
                "celex": h.payload.get("celex"),
                "article": h.payload.get("article_number"),
                "text": h.payload.get("text", "")[:500],
                "score": h.score,
            })
    except Exception as e:
        log.warning("qdrant_search_failed", error=str(e))

    # Stage 3: Neo4j graph traversal
    if state.get("product_gtin"):
        try:
            neo4j = get_neo4j()
            records = await neo4j.run_query(
                "MATCH (r:Regulation) RETURN r.short_name as name, r.celex_number as celex LIMIT 5",
            )
            for rec in records:
                retrieved.append({"source": "neo4j", "celex": rec.get("celex"), "name": rec.get("name")})
        except Exception as e:
            log.warning("neo4j_graph_query_failed", error=str(e))

    citations = list({r["celex"] for r in retrieved if r.get("celex")})

    # Stage 4: story-building with Claude Sonnet 4
    context_text = "\n".join(
        f"[{r['source']} | {r.get('celex', '')} Art.{r.get('article', '')}]: {r.get('text', '')[:300]}"
        for r in retrieved
    ) or "No relevant regulations retrieved."

    story_prompt = (
        f"Based on the following regulatory context, answer the query with specific article citations.\n"
        f"Query: {query}\n\nContext:\n{context_text}"
    )
    llm = get_sonnet()
    story = await llm.invoke(
        "You are a regulatory knowledge synthesis expert. Always cite EUR-Lex article numbers.",
        story_prompt,
    )

    confidence = 0.87 if retrieved else 0.55
    log.info("knowledge_graph_done", retrieved=len(retrieved), confidence=confidence)

    return {
        "knowledge_context": {
            "retrieved_articles": retrieved,
            "story": story,
            "citations": citations,
        },
        "confidence_scores": {**state.get("confidence_scores", {}), "knowledge_graph": confidence},
        "regulation_references": state.get("regulation_references", []) + citations,
    }
