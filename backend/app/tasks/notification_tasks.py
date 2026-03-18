"""Notification tasks — real implementations using notification_service."""

import asyncio

from app.tasks.celery_app import celery_app


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def notify_link_update(self, link_id: str, tenant_id: str):
    """Notify idea owners when a new cross-idea link is detected."""
    import uuid

    from app.database import async_session_factory
    from app.services.notification_service import NotificationService

    async def _notify():
        async with async_session_factory() as db:
            svc = NotificationService(db)
            await svc.notify_idea_owners_of_link(
                uuid.UUID(link_id), uuid.UUID(tenant_id)
            )

    try:
        _run(_notify())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def notify_dependency_cleared(self, dep_id: str, tenant_id: str):
    """Notify component owner when a blocking dependency target is marked 'done'."""
    import uuid

    from app.database import async_session_factory
    from app.services.notification_service import NotificationService

    async def _notify():
        async with async_session_factory() as db:
            svc = NotificationService(db)
            await svc.notify_dependency_cleared(
                uuid.UUID(dep_id), uuid.UUID(tenant_id)
            )

    try:
        _run(_notify())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def notify_cross_idea_dep_detected(self, dep_id: str, tenant_id: str):
    """Notify owners when a cross-idea dependency is detected."""
    import uuid

    from app.database import async_session_factory
    from app.services.notification_service import NotificationService

    async def _notify():
        async with async_session_factory() as db:
            svc = NotificationService(db)
            await svc.notify_cross_idea_dep_detected(
                uuid.UUID(dep_id), uuid.UUID(tenant_id)
            )

    try:
        _run(_notify())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def notify_shareability_change(component_id: str, old_tier: int, new_tier: int):
    """Placeholder — log shareability tier change for audit purposes."""
    # Could be expanded to notify team members if their visibility changes
    pass
