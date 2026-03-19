"""Celery tasks for cross-idea dependency detection."""

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
def detect_cross_idea_dependencies(self, idea_id: str, tenant_id: str):
    """Detect potential cross-idea dependencies for an idea's components."""
    async def _inner():
        from app.database import AsyncSessionLocal
        from app.llm.client import get_llm_client
        from app.services.dependency_service import DependencyService

        async with AsyncSessionLocal() as db:
            svc = DependencyService(db, get_llm_client())
            await svc.detect_cross_idea_dependencies(uuid.UUID(idea_id), uuid.UUID(tenant_id))

    try:
        _run(_inner())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def nightly_dependency_rescan(self):
    """Nightly sweep: re-run cross-idea dependency detection for all active ideas."""
    async def _inner():
        from sqlalchemy import select

        from app.database import AsyncSessionLocal
        from app.llm.client import get_llm_client
        from app.models.idea import Idea, IdeaStatus
        from app.models.user import Tenant
        from app.services.dependency_service import DependencyService

        async with AsyncSessionLocal() as db:
            tenants = list(await db.scalars(select(Tenant)))
            llm = get_llm_client()
            for tenant in tenants:
                active_ideas = list(
                    await db.scalars(
                        select(Idea).where(
                            Idea.tenant_id == tenant.id,
                            Idea.status == IdeaStatus.active,
                        )
                    )
                )
                svc = DependencyService(db, llm)
                for idea in active_ideas:
                    try:
                        await svc.detect_cross_idea_dependencies(idea.id, tenant.id)
                    except Exception:
                        pass  # advisory — don't abort the whole sweep

    try:
        _run(_inner())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)


@celery_app.task
def update_component_embedding(component_id: str, tenant_id: str):
    """Generate embedding for a component and trigger dependency detection."""
    async def _inner():
        from sqlalchemy import text

        from app.database import AsyncSessionLocal
        from app.llm.client import get_llm_client
        from app.models.idea import IdeaComponent
        from app.services.embedding_service import EmbeddingService

        async with AsyncSessionLocal() as db:
            comp = await db.get(IdeaComponent, uuid.UUID(component_id))
            if not comp:
                return
            svc = EmbeddingService(db, get_llm_client())
            text_content = f"{comp.name}\n{comp.description}"
            embedding = await svc.generate(text_content)
            await db.execute(
                text(
                    "UPDATE idea_components SET embedding = :emb::vector WHERE id = :id"
                ),
                {"emb": "[" + ",".join(str(v) for v in embedding) + "]", "id": str(comp.id)},
            )
            await db.commit()

    _run(_inner())
