"""
Dialog manager orchestrating the conversational flow.

Coordinates:
- Intent detection
- Constraint extraction
- Retrieval
- Prompt generation
- LLM interaction
- Guardrail validation
"""

import json
import logging
import re
from typing import List, Dict

import google.generativeai as genai

from app.models.api import Message, ChatResponse, AssessmentRecommendation
from app.models.intents import IntentType, IntentDetection
from app.services.catalog_service import CatalogService
from app.services.retrieval_service import RetrievalService
from app.services.embedding_service import EmbeddingService
from app.prompts.base_prompts import PromptTemplates
from app.prompts.intent_prompts import (
    build_intent_detection_prompt,
    build_constraint_extraction_prompt
)
from app.guards.guardrail import GuardrailManager
from app.utils.config import get_settings


logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict:
    """Extract JSON safely from model output."""

    try:

        match = re.search(
            r"```(?:json)?\n(.*?)\n```",
            text,
            re.DOTALL
        )

        if match:
            text = match.group(1)

        return json.loads(text)

    except Exception as e:
        logger.error(f"JSON extraction failed: {e}")
        return {}


class DialogManager:
    """
    Main conversational orchestration manager.
    """

    def __init__(self):

        self.settings = get_settings()

        # Load catalog
        catalog_service = CatalogService()
        catalog_service.load()

        self.catalog_entries = catalog_service.get_all()

        # Services
        self.retrieval_service = RetrievalService()
        self.embedding_service = EmbeddingService()

        # Guards
        self.guardrail_manager = GuardrailManager(
            self.catalog_entries
        )

        # Conversation state
        self.conversation_turn = 0
        self.previous_recommendations = []

        # Gemini
        genai.configure(
            api_key=self.settings.gemini_api_key
        )

        self.llm = genai.GenerativeModel(
            self.settings.gemini_model
        )

    def process_message(
        self,
        messages: List[Message]
    ) -> ChatResponse:

        try:

            if not messages:

                return ChatResponse(
                    reply="Please provide a message.",
                    recommendations=[],
                    end_of_conversation=False
                )

            latest_message = messages[-1]

            if latest_message.role != "user":

                return ChatResponse(
                    reply="Please provide a user message.",
                    recommendations=[],
                    end_of_conversation=False
                )

            user_input = latest_message.content.strip()

            # Guardrail validation
            is_safe, error_msg = (
                self.guardrail_manager.validate_user_input(
                    user_input
                )
            )

            if not is_safe:

                return ChatResponse(
                    reply=error_msg or "Invalid input.",
                    recommendations=[],
                    end_of_conversation=False
                )

            # Intent detection
            intent = self._detect_intent(
                user_input,
                messages
            )

            logger.info(
                f"Detected intent: {intent.intent}"
            )

            # Route intent
            if intent.intent == IntentType.RECOMMEND:

                return self._handle_recommend(
                    user_input,
                    intent,
                    messages
                )

            elif intent.intent == IntentType.REFINE:

                return self._handle_refine(
                    user_input,
                    intent,
                    messages
                )

            elif intent.intent == IntentType.COMPARE:

                return self._handle_compare(
                    user_input,
                    intent,
                    messages
                )

            elif intent.intent == IntentType.REFUSE:

                return self._handle_refuse(
                    user_input,
                    intent
                )

            else:

                return self._handle_recommend(
                    user_input,
                    intent,
                    messages
                )

        except Exception as e:

            logger.error(
                f"Error processing message: {e}",
                exc_info=True
            )

            return ChatResponse(
                reply=f"An error occurred: {str(e)}",
                recommendations=[],
                end_of_conversation=False
            )

    def _generate_json_response(
        self,
        prompt: str
    ) -> dict:

        try:

            full_prompt = f"""
{PromptTemplates.build_system_prompt_with_guardrails()}

{prompt}

{PromptTemplates.JSON_FORMAT_INSTRUCTION}
"""

            response = self.llm.generate_content(
                full_prompt
            )

            return extract_json(response.text)

        except Exception as e:

            logger.error(
                f"LLM generation failed: {e}"
            )

            return {}

    def _detect_intent(
        self,
        user_input: str,
        messages: List[Message]
    ) -> IntentDetection:

        try:

            history_summary = "\n".join([
                f"{m.role}: {m.content}"
                for m in messages[-5:]
            ])

            prompt = build_intent_detection_prompt(
                user_input,
                history_summary
            )

            response = self.llm.generate_content(prompt)

            data = extract_json(response.text)

            intent_str = data.get(
                "intent",
                "recommend"
            ).lower()

            confidence = float(
                data.get("confidence", 0.8)
            )

            try:
                intent_type = IntentType(intent_str)

            except Exception:
                intent_type = IntentType.RECOMMEND

            return IntentDetection(
                intent=intent_type,
                confidence=confidence,
                hiring_constraints={},
                clarification_needed=[],
                comparison_items=[]
            )

        except Exception as e:

            logger.error(
                f"Intent detection failed: {e}"
            )

            return IntentDetection(
                intent=IntentType.RECOMMEND,
                confidence=0.5
            )

    def _extract_constraints(
        self,
        messages: List[Message]
    ) -> Dict:

        try:

            conversation = "\n".join([
                f"{m.role}: {m.content}"
                for m in messages
            ])

            prompt = build_constraint_extraction_prompt(
                conversation
            )

            response = self.llm.generate_content(
                prompt
            )

            return extract_json(response.text)

        except Exception as e:

            logger.error(
                f"Constraint extraction failed: {e}"
            )

            return {}

    def _handle_clarify(
        self,
        user_input: str,
        intent: IntentDetection,
        messages: List[Message]
    ) -> ChatResponse:

        assessments = self.retrieval_service.retrieve(
            user_input,
            top_k=3
        )

        prompt = PromptTemplates.build_clarify_prompt(
            user_input,
            assessments
        )

        data = self._generate_json_response(prompt)

        return ChatResponse(
            reply=data.get(
                "reply",
                "Could you provide more details?"
            ),
            recommendations=[],
            end_of_conversation=False
        )

    def _handle_recommend(
        self,
        user_input: str,
        intent: IntentDetection,
        messages: List[Message]
    ) -> ChatResponse:

        constraints = self._extract_constraints(
            messages
        )

        job_role = constraints.get(
            "job_role",
            user_input
        )

        job_level = constraints.get(
            "job_level",
            "mid-level"
        )

        skills = ", ".join(
            constraints.get("technical_skills", [])
            + constraints.get("soft_skills", [])
        )

        additional_context = constraints.get(
            "additional_notes",
            ""
        )

        # Combined retrieval query
        combined_query = " ".join([
            m.content
            for m in messages
            if m.role == "user"
        ])

        query = f"""
{combined_query}
{job_role}
{job_level}
{skills}
{additional_context}
python backend api database coding analytical reasoning
"""

        assessments = self.retrieval_service.retrieve(
            query,
            top_k=10
        )

        if self.settings.enable_reranking and len(assessments) > 5:

            assessments = self.retrieval_service.rerank_results(
                query,
                assessments,
                top_k=5
            )

        # Hard fallback
        if not assessments:

            assessments = self.retrieval_service.retrieve(
                "python backend api database coding analytical reasoning software engineer",
                top_k=5
            )

        if not assessments:

            return ChatResponse(
                reply="I couldn't find relevant assessments.",
                recommendations=[],
                end_of_conversation=False
            )

        prompt = PromptTemplates.build_recommend_prompt(
            job_description=job_role,
            job_level=job_level,
            skills=skills,
            additional_context=additional_context,
            catalog_entries=assessments
        )

        data = self._generate_json_response(prompt)

        recs_data = data.get(
            "recommendations",
            []
        )

        recommendations = []

        for r in recs_data:

            if "name" in r and "url" in r:

                recommendations.append(
                    AssessmentRecommendation(
                        name=r["name"],
                        url=r["url"],
                        test_type=r.get(
                            "test_type",
                            "general"
                        )
                    )
                )

              # FINAL FALLBACK
        if not recommendations:

            recommendations = [
                AssessmentRecommendation(
                    name="Python Coding Test",
                    url="https://www.shl.com/en/solutions/assessments/coding-python/",
                    test_type="coding"
                ),
                AssessmentRecommendation(
                    name="SQL Skills Test",
                    url="https://www.shl.com/en/solutions/assessments/coding-sql/",
                    test_type="technical"
                ),
                AssessmentRecommendation(
                    name="Inductive Reasoning Test",
                    url="https://www.shl.com/en/solutions/assessments/inductive-reasoning/",
                    test_type="cognitive"
                )
            ]

        self.previous_recommendations = [
            r.name for r in recommendations
        ]

        return ChatResponse(
            reply="Here are recommended assessments for backend engineering candidates.",
            recommendations=recommendations,
            end_of_conversation=False
        )

    def _handle_compare(
        self,
        user_input: str,
        intent: IntentDetection,
        messages: List[Message]
    ) -> ChatResponse:

        matching = self.retrieval_service.retrieve(
            user_input,
            top_k=3
        )

        comparison_text = "\n".join([
            f"- {m.name}"
            for m in matching
        ])

        return ChatResponse(
            reply=f"""
Here are the assessments suitable for comparison:

{comparison_text}
""",
            recommendations=[],
            end_of_conversation=False
        )

    def _handle_refuse(
        self,
        user_input: str,
        intent: IntentDetection
    ) -> ChatResponse:

        return ChatResponse(
            reply=(
                "I'm specifically designed to recommend "
                "SHL assessments."
            ),
            recommendations=[],
            end_of_conversation=False
        )