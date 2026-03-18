"""Embedding service — generates vectors and performs similarity search via pgvector."""

import math
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.llm.client import LLMClient


class EmbeddingService:
    def __init__(self, db: AsyncSession, llm_client: LLMClient):
        self.db = db
        self.llm = llm_client

    async def generate(self, text: str) -> list[float]:
        """Generate a 768-dim embedding for the given text."""
        return await self.llm.embed(settings.llm_embedding_model, text)

    @staticmethod
    def cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(a * b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a * a for a in v1))
        mag2 = math.sqrt(sum(b * b for b in v2))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)

    async def find_similar_ideas(
        self,
        embedding: list[float],
        tenant_id: str,
        exclude_idea_id: str | None = None,
        threshold: float = 0.7,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Find ideas with similar embeddings using pgvector cosine similarity."""
        vector_str = "[" + ",".join(str(v) for v in embedding) + "]"
        exclude_clause = f"AND id != '{exclude_idea_id}'" if exclude_idea_id else ""

        result = await self.db.execute(
            text(f"""
                SELECT id, title, description,
                       1 - (embedding <=> :embedding::vector) as similarity
                FROM ideas
                WHERE tenant_id = :tenant_id
                  AND embedding IS NOT NULL
                  AND status != 'archived'
                  {exclude_clause}
                  AND 1 - (embedding <=> :embedding::vector) >= :threshold
                ORDER BY embedding <=> :embedding::vector
                LIMIT :limit
            """),
            {"embedding": vector_str, "tenant_id": tenant_id, "threshold": threshold, "limit": limit},
        )
        return [dict(row._mapping) for row in result]

    async def find_similar_components(
        self,
        embedding: list[float],
        tenant_id: str,
        exclude_component_id: str | None = None,
        threshold: float = 0.75,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Find components with similar embeddings."""
        vector_str = "[" + ",".join(str(v) for v in embedding) + "]"
        exclude_clause = (
            f"AND ic.id != '{exclude_component_id}'" if exclude_component_id else ""
        )

        result = await self.db.execute(
            text(f"""
                SELECT ic.id, ic.idea_id, ic.name, ic.description,
                       i.title as idea_title,
                       1 - (ic.embedding <=> :embedding::vector) as similarity
                FROM idea_components ic
                JOIN ideas i ON i.id = ic.idea_id
                WHERE ic.tenant_id = :tenant_id
                  AND ic.embedding IS NOT NULL
                  {exclude_clause}
                ORDER BY ic.embedding <=> :embedding::vector
                LIMIT :limit
            """),
            {"embedding": vector_str, "tenant_id": tenant_id, "limit": limit},
        )
        rows = [dict(row._mapping) for row in result]
        return [r for r in rows if r["similarity"] >= threshold]
