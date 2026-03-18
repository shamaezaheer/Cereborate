"""LLM service — wraps LLMClient with prompt rendering and response parsing."""

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config import settings
from app.llm.client import LLMClient
from app.llm.schemas import (
    ConsistencyCheckResult,
    DependencyDetectionResult,
    ExtractedIdeaData,
    LinkDetectionResult,
    QuestionAnswerResult,
    ShareabilityScore,
)

PROMPTS_DIR = Path(__file__).parent.parent / "llm" / "prompts"

_jinja_env = Environment(
    loader=FileSystemLoader(str(PROMPTS_DIR)),
    autoescape=False,
)
_jinja_env.filters["tojson"] = json.dumps


class LLMService:
    def __init__(self, client: LLMClient):
        self.client = client

    def _render(self, template_name: str, **kwargs: object) -> str:
        return _jinja_env.get_template(template_name).render(**kwargs)

    async def extract_idea_from_conversation(
        self, conversation: list[dict]
    ) -> ExtractedIdeaData:
        system_prompt = self._render("planning_intake.j2")
        messages = [{"role": "system", "content": system_prompt}] + conversation
        result = await self.client.chat_json(
            model=settings.llm_planning_model, messages=messages
        )
        return ExtractedIdeaData.model_validate(result)

    async def generate_follow_up(
        self, conversation: list[dict], extracted_data: dict
    ) -> str:
        system = self._render(
            "follow_up.j2",
            conversation=conversation,
            extracted_data=extracted_data,
        )
        messages = [{"role": "system", "content": system}]
        return await self.client.chat(
            model=settings.llm_planning_model, messages=messages, temperature=0.5
        )

    async def score_shareability(
        self, component: dict, idea_context: str
    ) -> ShareabilityScore:
        system = "You are a data classification assistant."
        prompt = self._render(
            "shareability_score.j2", component=component, idea_context=idea_context
        )
        result = await self.client.chat_json(
            model=settings.llm_classifier_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return ShareabilityScore.model_validate(result)

    async def detect_link(
        self, idea_a: dict, idea_b: dict, similarity_score: float
    ) -> LinkDetectionResult:
        prompt = self._render(
            "link_detection.j2",
            idea_a=idea_a,
            idea_b=idea_b,
            similarity_score=round(similarity_score, 4),
        )
        result = await self.client.chat_json(
            model=settings.llm_planning_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return LinkDetectionResult.model_validate(result)

    async def detect_dependency(
        self, comp_a: dict, comp_b: dict, similarity_score: float
    ) -> DependencyDetectionResult:
        prompt = self._render(
            "dependency_detection.j2",
            comp_a=comp_a,
            comp_b=comp_b,
            similarity_score=round(similarity_score, 4),
        )
        result = await self.client.chat_json(
            model=settings.llm_planning_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return DependencyDetectionResult.model_validate(result)

    async def check_consistency(
        self, idea: dict, components: list[dict], cross_idea_context: str | None = None
    ) -> ConsistencyCheckResult:
        prompt = self._render(
            "consistency_check.j2",
            idea=idea,
            components=components,
            cross_idea_context=cross_idea_context,
        )
        result = await self.client.chat_json(
            model=settings.llm_planning_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return ConsistencyCheckResult.model_validate(result)

    async def answer_question(
        self, idea: dict, components: list[dict], question: str, prior_answers: list[dict]
    ) -> QuestionAnswerResult:
        prompt = self._render(
            "question_answer.j2",
            idea=idea,
            components=components,
            question=question,
            prior_answers=prior_answers,
        )
        result = await self.client.chat_json(
            model=settings.llm_planning_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return QuestionAnswerResult.model_validate(result)
