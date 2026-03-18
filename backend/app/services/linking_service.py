"""Linking service — detects semantic relationships between ideas via embeddings + LLM."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMClient
from app.models.idea import Idea
from app.models.link import IdeaLink
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService

SIMILARITY_THRESHOLD = 0.72  # Minimum cosine similarity to trigger LLM link check


class LinkingService:
    def __init__(self, db: AsyncSession, llm_client: LLMClient):
        self.db = db
        self.embedding_svc = EmbeddingService(db, llm_client)
        self.llm_svc = LLMService(llm_client)

    async def update_idea_embedding(self, idea_id: uuid.UUID) -> None:
        """Generate and store embedding for an idea."""
        idea = await self.db.get(Idea, idea_id)
        if not idea:
            return

        text = f"{idea.title}\n{idea.description}"
        embedding = await self.embedding_svc.generate(text)

        idea.embedding = embedding
        await self.db.commit()

    async def detect_links_for_idea(self, idea_id: uuid.UUID, tenant_id: uuid.UUID) -> list[IdeaLink]:
        """Find and create links for an idea based on embedding similarity."""
        idea = await self.db.get(Idea, idea_id)
        if not idea or idea.embedding is None:
            return []

        similar = await self.embedding_svc.find_similar_ideas(
            embedding=idea.embedding,
            tenant_id=str(tenant_id),
            exclude_idea_id=str(idea_id),
            threshold=SIMILARITY_THRESHOLD,
        )

        created_links = []
        for candidate in similar:
            candidate_idea = await self.db.get(Idea, uuid.UUID(str(candidate["id"])))
            if not candidate_idea:
                continue

            # Check if link already exists
            existing = await self.db.scalar(
                select(IdeaLink).where(
                    (
                        (IdeaLink.source_idea_id == idea_id)
                        & (IdeaLink.target_idea_id == candidate_idea.id)
                    )
                    | (
                        (IdeaLink.source_idea_id == candidate_idea.id)
                        & (IdeaLink.target_idea_id == idea_id)
                    )
                )
            )
            if existing:
                continue

            # Use LLM to confirm and classify the link
            result = await self.llm_svc.detect_link(
                idea_a={"title": idea.title, "description": idea.description},
                idea_b={"title": candidate_idea.title, "description": candidate_idea.description},
                similarity_score=float(candidate["similarity"]),
            )

            if result.linked and result.confidence >= 0.6:
                link = IdeaLink(
                    tenant_id=tenant_id,
                    source_idea_id=idea_id,
                    target_idea_id=candidate_idea.id,
                    link_type=result.link_type or "related",
                    similarity_score=float(candidate["similarity"]),
                    llm_rationale=result.similarity_rationale,
                    confirmed=False,
                )
                self.db.add(link)
                created_links.append(link)

        if created_links:
            await self.db.commit()

        return created_links

    async def get_idea_links(self, idea_id: uuid.UUID) -> list[IdeaLink]:
        """Get all links for an idea."""
        links = await self.db.scalars(
            select(IdeaLink).where(
                (IdeaLink.source_idea_id == idea_id)
                | (IdeaLink.target_idea_id == idea_id)
            )
        )
        return list(links)
