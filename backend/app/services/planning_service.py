"""Planning service — orchestrates idea intake from conversational session to created idea."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMClient
from app.models.idea import (
    ComponentPriority,
    ComponentStatus,
    Idea,
    IdeaComponent,
    IdeaStatus,
    IdeaVersion,
    PlanningSession,
    PlanningSessionStatus,
)
from app.services.llm_service import LLMService


class PlanningService:
    def __init__(self, db: AsyncSession, llm_client: LLMClient):
        self.db = db
        self.llm = LLMService(llm_client)

    async def start_session(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID, initial_message: str
    ) -> PlanningSession:
        """Start a new planning session with the user's first message."""
        conversation = [{"role": "user", "content": initial_message}]

        # Extract what we can from the first message
        extraction = await self.llm.extract_idea_from_conversation(conversation)
        extracted_data = extraction.model_dump()

        # Add assistant follow-up to conversation
        if extraction.follow_up_question:
            conversation.append({
                "role": "assistant",
                "content": extraction.follow_up_question,
            })

        session = PlanningSession(
            tenant_id=tenant_id,
            user_id=user_id,
            mode="chat",
            status="active",
            conversation_history=conversation,
            extracted_data=extracted_data,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def respond(
        self, session_id: uuid.UUID, user_message: str
    ) -> tuple[PlanningSession, str]:
        """Process a user response and return updated session + assistant message."""
        session = await self.db.get(PlanningSession, session_id)
        if not session or session.status != PlanningSessionStatus.active:
            raise ValueError("Session not found or not active")

        # Append user message
        history = list(session.conversation_history)
        history.append({"role": "user", "content": user_message})

        # Re-extract from full conversation
        extraction = await self.llm.extract_idea_from_conversation(history)
        extracted_data = extraction.model_dump()

        assistant_msg = ""
        if extraction.is_complete:
            assistant_msg = (
                "I have everything I need! Ready to create your idea. "
                "You can review the details and confirm, or keep chatting to refine further."
            )
        elif extraction.follow_up_question:
            assistant_msg = extraction.follow_up_question
        else:
            assistant_msg = "Got it! Is there anything else you'd like to add?"

        history.append({"role": "assistant", "content": assistant_msg})

        # Update session
        session.conversation_history = history
        session.extracted_data = extracted_data
        await self.db.commit()
        await self.db.refresh(session)

        return session, assistant_msg

    async def complete_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[PlanningSession, Idea]:
        """Finalize session and create the Idea with components."""
        session = await self.db.get(PlanningSession, session_id)
        if not session:
            raise ValueError("Session not found")

        data = session.extracted_data

        idea = Idea(
            tenant_id=session.tenant_id,
            creator_id=user_id,
            title=data.get("title") or "Untitled Idea",
            description=data.get("description") or "",
            status=IdeaStatus.draft,
            deadline=(
                datetime.fromisoformat(data["deadline"])
                if data.get("deadline")
                else None
            ),
            total_budget=(
                Decimal(str(data["total_budget"])) if data.get("total_budget") else None
            ),
            budget_currency=data.get("budget_currency", "USD"),
            version=1,
        )
        self.db.add(idea)
        await self.db.flush()

        # Save initial version snapshot
        version = IdeaVersion(
            tenant_id=session.tenant_id,
            idea_id=idea.id,
            version=1,
            snapshot={
                "title": idea.title,
                "description": idea.description,
                "status": idea.status,
            },
            changed_by=user_id,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(version)

        # Create components
        for comp_data in data.get("components", []):
            priority_str = comp_data.get("priority", "should_have")
            try:
                priority = ComponentPriority(priority_str)
            except ValueError:
                priority = ComponentPriority.should_have

            component = IdeaComponent(
                tenant_id=session.tenant_id,
                idea_id=idea.id,
                name=comp_data.get("name", ""),
                description=comp_data.get("description", ""),
                priority=priority,
                status=ComponentStatus.proposed,
                estimated_cost=(
                    Decimal(str(comp_data["estimated_cost"]))
                    if comp_data.get("estimated_cost")
                    else None
                ),
            )
            self.db.add(component)

        # Complete session
        session.idea_id = idea.id
        session.status = PlanningSessionStatus.completed
        session.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(idea)
        await self.db.refresh(session)

        return session, idea

    async def get_session(self, session_id: uuid.UUID) -> PlanningSession | None:
        return await self.db.get(PlanningSession, session_id)
