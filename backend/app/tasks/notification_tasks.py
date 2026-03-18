"""Notification tasks — stubs for Phase 5 implementation."""

import asyncio

from app.tasks.celery_app import celery_app


@celery_app.task
def notify_link_update(idea_id: str, linked_idea_id: str, link_type: str):
    """Notify idea owner when a new cross-idea link is detected."""
    # Phase 5: implement with notification_service
    pass


@celery_app.task
def notify_dependency_cleared(source_component_id: str, target_component_id: str):
    """Notify component owner when a blocking dependency target is marked 'done'."""
    # Phase 5: implement with notification_service
    pass


@celery_app.task
def notify_shareability_change(component_id: str, old_tier: int, new_tier: int):
    """Notify team members when shareability tier changes affect their visibility."""
    # Phase 5: implement with notification_service
    pass
