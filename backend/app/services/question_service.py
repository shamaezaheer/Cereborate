"""Question service — team Q&A with LLM-assisted answers and access filtering."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMClient
from app.models.discussion import Answer, Question
from app.models.idea import Idea, IdeaComponent
from app.models.shareability import ShareabilityRule
from app.services.llm_service import LLMService


class QuestionService:
    def __init__(self, db: AsyncSession, llm_client: LLMClient):
        self.db = db
        self.llm_svc = LLMService(llm_client)

    async def ask_question(
        self,
        idea_id: uuid.UUID,
        asked_by: uuid.UUID,
        question_text: str,
        tenant_id: uuid.UUID,
        component_id: uuid.UUID | None = None,
    ) -> Question:
        """Create a new question on a shared idea."""
        idea = await self.db.scalar(
            select(Idea).where(Idea.id == idea_id, Idea.tenant_id == tenant_id)
        )
        if not idea:
            raise ValueError("Idea not found")

        question = Question(
            tenant_id=tenant_id,
            idea_id=idea_id,
            component_id=component_id,
            asked_by=asked_by,
            question_text=question_text,
        )
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def get_questions(
        self,
        idea_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_tier: int,
    ) -> list[Question]:
        """Get questions for an idea, filtered to those whose component is visible."""
        all_q = list(
            await self.db.scalars(
                select(Question).where(
                    Question.idea_id == idea_id,
                    Question.tenant_id == tenant_id,
                )
            )
        )

        visible = []
        for q in all_q:
            if q.component_id is None:
                visible.append(q)
                continue
            # Check component shareability
            rule = await self.db.scalar(
                select(ShareabilityRule).where(
                    ShareabilityRule.component_id == q.component_id,
                    ShareabilityRule.tenant_id == tenant_id,
                )
            )
            if rule is None or rule.min_access_tier <= user_tier:
                visible.append(q)

        return visible

    async def get_answers(
        self, question_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[Answer]:
        """Get all approved answers (and unapproved own AI answers)."""
        return list(
            await self.db.scalars(
                select(Answer).where(
                    Answer.question_id == question_id,
                    Answer.tenant_id == tenant_id,
                )
            )
        )

    async def answer_question(
        self,
        question_id: uuid.UUID,
        answered_by: uuid.UUID,
        answer_text: str,
        tenant_id: uuid.UUID,
    ) -> Answer:
        """Submit a human answer to a question."""
        question = await self.db.scalar(
            select(Question).where(
                Question.id == question_id, Question.tenant_id == tenant_id
            )
        )
        if not question:
            raise ValueError("Question not found")

        answer = Answer(
            tenant_id=tenant_id,
            question_id=question_id,
            answered_by=answered_by,
            answer_text=answer_text,
            is_ai_generated=False,
            approved=True,  # human answers auto-approved
        )
        self.db.add(answer)

        # Update question status
        question.status = "answered"
        await self.db.commit()
        await self.db.refresh(answer)
        return answer

    async def generate_ai_answer(
        self, question_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Answer:
        """Generate an LLM-drafted answer. Requires owner approval before display."""
        question = await self.db.scalar(
            select(Question).where(
                Question.id == question_id, Question.tenant_id == tenant_id
            )
        )
        if not question:
            raise ValueError("Question not found")

        idea = await self.db.get(Idea, question.idea_id)
        if not idea:
            raise ValueError("Idea not found")

        components = list(
            await self.db.scalars(
                select(IdeaComponent).where(IdeaComponent.idea_id == question.idea_id)
            )
        )

        prior_answers = list(
            await self.db.scalars(
                select(Answer).where(Answer.question_id == question_id)
            )
        )

        result = await self.llm_svc.answer_question(
            idea={
                "title": idea.title,
                "description": idea.description,
                "status": idea.status,
            },
            components=[
                {
                    "name": c.name,
                    "description": c.description,
                    "status": c.status,
                    "priority": c.priority,
                }
                for c in components
            ],
            question=question.question_text,
            prior_answers=[
                {"answer": a.answer_text, "ai": a.is_ai_generated}
                for a in prior_answers
            ],
        )

        answer = Answer(
            tenant_id=tenant_id,
            question_id=question_id,
            answered_by=None,
            answer_text=result.answer,
            is_ai_generated=True,
            approved=not result.needs_owner_approval,
        )
        self.db.add(answer)
        await self.db.commit()
        await self.db.refresh(answer)
        return answer

    async def approve_answer(
        self, answer_id: uuid.UUID, user_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Answer:
        """Idea owner approves an AI-generated answer."""
        answer = await self.db.scalar(
            select(Answer).where(
                Answer.id == answer_id, Answer.tenant_id == tenant_id
            )
        )
        if not answer:
            raise ValueError("Answer not found")

        question = await self.db.get(Question, answer.question_id)
        if not question:
            raise ValueError("Question not found")

        # Verify user owns the idea
        idea = await self.db.get(Idea, question.idea_id)
        if not idea or str(idea.creator_id) != str(user_id):
            raise PermissionError("Only the idea owner can approve AI answers")

        answer.approved = True
        await self.db.commit()
        await self.db.refresh(answer)
        return answer
