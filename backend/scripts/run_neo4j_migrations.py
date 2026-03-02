#!/usr/bin/env python3
"""
Run Neo4j Cypher migrations from backend/migrations/neo4j/.
Usage: python -m scripts.run_neo4j_migrations
"""
import asyncio
from pathlib import Path

from neo4j import AsyncGraphDatabase
import os

def get_uri_and_auth():
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    auth_s = os.environ.get("NEO4J_AUTH", "neo4j/dpp-neo4j-dev")
    if "/" in auth_s:
        u, p = auth_s.split("/", 1)
        return uri, (u.strip(), p.strip())
    return uri, ("neo4j", auth_s)


async def main():
    uri, auth = get_uri_and_auth()
    driver = AsyncGraphDatabase.driver(uri, auth=auth)
    migrations_dir = Path(__file__).resolve().parent.parent / "migrations" / "neo4j"
    cypher_files = sorted(migrations_dir.glob("*.cypher"))
    async with driver.session() as session:
        for f in cypher_files:
            text = f.read_text()
            # Run each statement (split by semicolon, skip comments and empty)
            for stmt in text.split(";"):
                stmt = stmt.strip()
                if not stmt or stmt.startswith("//"):
                    continue
                try:
                    await session.run(stmt)
                    print(f"OK: {f.name} -> {stmt[:60]}...")
                except Exception as e:
                    print(f"SKIP/ERROR: {stmt[:60]}... -> {e}")
    await driver.close()
    print("Migrations done.")


if __name__ == "__main__":
    asyncio.run(main())
