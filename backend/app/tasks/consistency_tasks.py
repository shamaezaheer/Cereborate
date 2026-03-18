"""Celery tasks for consistency checking."""

import asyncio
import uuid

from app.tasks.celery_app import celery_app


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=2)
def run_idea_consistency_check(self, idea_id: str, tenant_id: str):
    """Run all consistency checks for a single idea."""
    async def _inner():
        from app.database import AsyncSessionLocal
        from app.llm.client import get_llm_client
        from app.services.consistency_service import ConsistencyService

        async with AsyncSessionLocal() as db:
            svc = ConsistencyService(db, get_llm_client())
            await svc.run_all_checks(uuid.UUID(idea_id), uuid.UUID(tenant_id))

    try:
        _run(_inner())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task
def nightly_consistency_sweep():
    """Nightly sweep: run consistency checks on all active ideas across all tenants."""
    async def _inner():
        from sqlalchemy import select

        from app.database import AsyncSessionLocal
        from app.llm.client import get_llm_client
        from app.models.idea import Idea, IdeaStatus
        from app.services.consistency_service import ConsistencyService

        async with AsyncSessionLocal() as db:
            ideas = list(await db.scalars(
                select(Idea).where(Idea.status == IdeaStatus.active)
            ))
            for idea in ideas:
                svc = ConsistencyService(db, get_llm_client())
                await svc.run_all_checks(idea.id, idea.tenant_id)

    _run(_inner())
