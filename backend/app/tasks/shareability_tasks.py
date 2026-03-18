"""Shareability tasks — background classification triggered on component create/update."""

import asyncio

from app.tasks.celery_app import celery_app


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def classify_component_shareability(self, component_id: str, tenant_id: str):
    """Classify a component's shareability using the LLM."""
    import uuid

    from app.database import async_session_factory
    from app.llm.client import get_llm_client
    from app.services.shareability_service import ShareabilityService

    async def _classify():
        async with async_session_factory() as db:
            svc = ShareabilityService(db, get_llm_client())
            await svc.classify_component(
                uuid.UUID(component_id), uuid.UUID(tenant_id)
            )

    try:
        _run(_classify())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def auto_expose_cross_idea_dependency(self, dep_id: str, tenant_id: str):
    """When a cross-idea dependency is confirmed, auto-expose both components."""
    import uuid

    from app.database import async_session_factory
    from app.llm.client import get_llm_client
    from app.services.shareability_service import ShareabilityService

    async def _expose():
        async with async_session_factory() as db:
            svc = ShareabilityService(db, get_llm_client())
            await svc.auto_expose_cross_idea_dep(
                uuid.UUID(dep_id), uuid.UUID(tenant_id)
            )

    try:
        _run(_expose())
    except Exception as exc:
        raise self.retry(exc=exc)
