"""Notification service — create and deliver event-driven alerts."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dependency import ComponentDependency
from app.models.idea import Idea, IdeaComponent
from app.models.link import IdeaLink
from app.models.notification import Notification
from app.models.user import TenantMembership


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: uuid.UUID,
        event_type: str,
        tenant_id: uuid.UUID,
        message: str,
        idea_id: uuid.UUID | None = None,
        component_id: uuid.UUID | None = None,
    ) -> Notification:
        notif = Notification(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            idea_id=idea_id,
            component_id=component_id,
            message=message,
        )
        self.db.add(notif)
        await self.db.flush()
        return notif

    async def get_notifications(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        unread_only: bool = False,
    ) -> list[Notification]:
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.tenant_id == tenant_id,
        )
        if unread_only:
            query = query.where(Notification.read.is_(False))
        return list(await self.db.scalars(query.order_by(Notification.created_at.desc())))

    async def mark_read(
        self, notification_id: uuid.UUID, user_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Notification:
        notif = await self.db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.tenant_id == tenant_id,
            )
        )
        if not notif:
            raise ValueError("Notification not found")
        notif.read = True
        await self.db.commit()
        return notif

    async def notify_idea_owners_of_link(
        self, link_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> None:
        """Notify owners of both ideas when a cross-idea link is detected."""
        link = await self.db.scalar(
            select(IdeaLink).where(IdeaLink.id == link_id)
        )
        if not link:
            return

        source = await self.db.get(Idea, link.source_idea_id)
        target = await self.db.get(Idea, link.target_idea_id)

        if source and source.creator_id:
            await self.create(
                user_id=source.creator_id,
                event_type="linked_idea_updated",
                tenant_id=tenant_id,
                idea_id=source.id,
                message=(
                    f"Your idea '{source.title}' has been linked to "
                    f"'{target.title if target else 'another idea'}'. "
                    f"Link type: {link.link_type}."
                ),
            )

        if target and target.creator_id and target.creator_id != (source.creator_id if source else None):
            await self.create(
                user_id=target.creator_id,
                event_type="linked_idea_updated",
                tenant_id=tenant_id,
                idea_id=target.id,
                message=(
                    f"Your idea '{target.title}' has been linked to "
                    f"'{source.title if source else 'another idea'}'. "
                    f"Link type: {link.link_type}."
                ),
            )

        await self.db.commit()

    async def notify_dependency_cleared(
        self, dep_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> None:
        """Notify source component owner when a blocking dependency is cleared."""
        dep = await self.db.scalar(
            select(ComponentDependency).where(ComponentDependency.id == dep_id)
        )
        if not dep or dep.dependency_type != "blocks":
            return

        source_comp = await self.db.get(IdeaComponent, dep.source_component_id)
        target_comp = await self.db.get(IdeaComponent, dep.target_component_id)

        if not source_comp or not target_comp:
            return

        source_idea = await self.db.get(Idea, source_comp.idea_id)
        if source_idea and source_idea.creator_id:
            await self.create(
                user_id=source_idea.creator_id,
                event_type="dependency_cleared",
                tenant_id=tenant_id,
                idea_id=source_idea.id,
                component_id=source_comp.id,
                message=(
                    f"Blocker cleared: '{target_comp.name}' is now done. "
                    f"'{source_comp.name}' can proceed."
                ),
            )

        await self.db.commit()

    async def notify_cross_idea_dep_detected(
        self,
        dep_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> None:
        """Notify owners of both ideas when a cross-idea dependency is detected."""
        dep = await self.db.scalar(
            select(ComponentDependency).where(ComponentDependency.id == dep_id)
        )
        if not dep or not dep.is_cross_idea:
            return

        source_comp = await self.db.get(IdeaComponent, dep.source_component_id)
        target_comp = await self.db.get(IdeaComponent, dep.target_component_id)

        if not source_comp or not target_comp:
            return

        source_idea = await self.db.get(Idea, source_comp.idea_id)
        target_idea = await self.db.get(Idea, target_comp.idea_id)

        for idea, other_idea, comp in [
            (source_idea, target_idea, source_comp),
            (target_idea, source_idea, target_comp),
        ]:
            if idea and idea.creator_id:
                await self.create(
                    user_id=idea.creator_id,
                    event_type="cross_idea_dep_detected",
                    tenant_id=tenant_id,
                    idea_id=idea.id,
                    component_id=comp.id,
                    message=(
                        f"Cross-idea dependency detected: '{source_comp.name}' "
                        f"({dep.dependency_type}) '{target_comp.name}'. "
                        f"{'Auto-exposure pending review.' if not dep.confirmed else 'Teams have been notified.'}"
                    ),
                )

        await self.db.commit()
