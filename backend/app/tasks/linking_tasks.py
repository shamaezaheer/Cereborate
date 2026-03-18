"""Celery tasks for embedding generation and cross-idea link detection."""

import asyncio
import uuid

from app.tasks.celery_app import celery_app


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def update_idea_embedding(self, idea_id: str, tenant_id: str):
    """Generate and store embedding for an idea, then trigger link detection."""
    async def _inner():
        from app.database import AsyncSessionLocal
        from app.llm.client import get_llm_client
        from app.services.linking_service import LinkingService

        async with AsyncSessionLocal() as db:
            svc = LinkingService(db, get_llm_client())
            await svc.update_idea_embedding(uuid.UUID(idea_id))
            await svc.detect_links_for_idea(uuid.UUID(idea_id), uuid.UUID(tenant_id))

    try:
        _run(_inner())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@celery_app.task
def scan_unlinked_ideas():
    """Periodic task: find ideas without embeddings and generate them."""
    async def _inner():
        from sqlalchemy import select, text

        from app.database import AsyncSessionLocal
        from app.llm.client import get_llm_client
        from app.models.idea import Idea
        from app.services.linking_service import LinkingService

        async with AsyncSessionLocal() as db:
            ideas = list(await db.scalars(
                select(Idea).where(Idea.embedding.is_(None), Idea.status != "archived")
            ))
            for idea in ideas:
                svc = LinkingService(db, get_llm_client())
                await svc.update_idea_embedding(idea.id)

    _run(_inner())
