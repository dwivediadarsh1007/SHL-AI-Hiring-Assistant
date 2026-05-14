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
from typing import List, Dict, Optional, Tuple

import google.generativeai as genai

from app.models.api import Message, ChatResponse, AssessmentRecommendation
from app.models.intents import IntentType, IntentDetection
from app.models.catalog import CatalogEntry
from app.services.catalog_service import CatalogService
from app.services.retrieval_service import RetrievalService
from app.services.embedding_service import EmbeddingService
from app.prompts.base_prompts import PromptTemplates
from app.prompts.intent_prompts import build_intent_detection_prompt, build_constraint_extraction_prompt
from app.guards.guardrail import GuardrailManager
from app.utils.config import get_settings


logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict:
    """Helper to extract JSON from LLM response which might have markdown fences."""
    try:
        # Check if the string has markdown json blocks
        match = re.search(r"```(?:json)?\n(.*?)\n```", text, re.DOTALL)
        if match:
            text = match.group(1)
        
        return json.loads(text)
    except Exception as e:
        logger.error(f"Failed to extract JSON from text: {text[:100]}... Error: {e}")
        return {}


class DialogManager:
    """
    Manages conversational flow for assessment recommendations.
    
    Responsibilities:
    - Parse conversation history
    - Detect user intent
    - Retrieve relevant assessments
    - Generate grounded responses
    - Validate all outputs
    """
    
    def __init__(self):
        """Initialize dialog manager."""
        self.settings = get_settings()
        
        # Load catalog
        catalog_service = CatalogService()
        catalog_service.load()
        self.catalog_entries = catalog_service.get_all()
        self.catalog_map = {entry.url: entry for entry in self.catalog_entries}
        
        # Initialize services
        self.retrieval_service = RetrievalService()
        self.embedding_service = EmbeddingService()
        
        # Initialize guards
        self.guardrail_manager = GuardrailManager(self.catalog_entries)
        
        # Conversation state
        self.conversation_turn = 0
        self.previous_recommendations: List[str] = []
        
        # Initialize LLM
        genai.configure(api_key=self.settings.gemini_api_key)
        self.llm = genai.GenerativeModel(self.settings.gemini_model)
    
    def process_message(self, messages: List[Message]) -> ChatResponse:
        """
        Process conversation and generate response.
        
        Args:
            messages: Full conversation history
            
        Returns:
            ChatResponse with reply and recommendations
        """
        try:
            self.conversation_turn = len(messages) // 2
            
            # Validate input
            if not messages or len(messages) == 0:
                return ChatResponse(
                    reply="Please provide a message",
                    recommendations=[],
                    end_of_conversation=False
                )
            
            # Get latest user message
            latest_message = messages[-1]
            if latest_message.role != "user":
                return ChatResponse(
                    reply="Please provide a user message",
                    recommendations=[],
                    end_of_conversation=False
                )
            
            user_input = latest_message.content.strip()
            
            # Check for injection
            is_safe, error_msg = self.guardrail_manager.validate_user_input(user_input)
            if not is_safe:
                return ChatResponse(
                    reply=error_msg or "I couldn't process that message.",
                    recommendations=[],
                    end_of_conversation=False
                )
            
            # 1. Detect intent using LLM
            intent = self._detect_intent(user_input, messages)
            logger.info(f"Detected intent: {intent.intent} (confidence: {intent.confidence:.2f})")
            
            # Handle based on intent
            if intent.intent == IntentType.CLARIFY:
                response = self._handle_clarify(user_input, intent, messages)
            elif intent.intent == IntentType.RECOMMEND:
                response = self._handle_recommend(user_input, intent, messages)
            elif intent.intent == IntentType.REFINE:
                response = self._handle_refine(user_input, intent, messages)
            elif intent.intent == IntentType.COMPARE:
                response = self._handle_compare(user_input, intent, messages)
            elif intent.intent == IntentType.REFUSE:
                response = self._handle_refuse(user_input, intent)
            else:
                response = ChatResponse(
                    reply="I'm not sure how to help with that.",
                    recommendations=[],
                    end_of_conversation=False
                )
            
            # Add previous recommendations logic tracking
            if response.recommendations:
                self.previous_recommendations = [r.name for r in response.recommendations]
                
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return ChatResponse(
                reply=f"An error occurred while processing your request: {str(e)}",
                recommendations=[],
                end_of_conversation=False
            )
            
    def _generate_llm_response(self, prompt: str) -> str:
        """Helper to generate text using the LLM with the system prompt context."""
        full_prompt = f"{PromptTemplates.build_system_prompt_with_guardrails()}\n\n{prompt}"
        response = self.llm.generate_content(full_prompt)
        return response.text

    def _generate_json_response(self, prompt: str) -> dict:
        """Helper to generate JSON output using the LLM."""
        full_prompt = f"{PromptTemplates.build_system_prompt_with_guardrails()}\n\n{prompt}\n\n{PromptTemplates.JSON_FORMAT_INSTRUCTION}"
        response = self.llm.generate_content(full_prompt)
        return extract_json(response.text)
    
    def _detect_intent(self, user_input: str, messages: List[Message]) -> IntentDetection:
        """
        Detect intent from user message and conversation history.
        """
        # Create a summary of history
        history_summary = "\\n".join([f"{m.role}: {m.content}" for m in messages[-5:]])
        prompt = build_intent_detection_prompt(user_input, history_summary)
        
        try:
            full_prompt = f"{PromptTemplates.build_system_prompt_with_guardrails()}\n\n{prompt}"
            response = self.llm.generate_content(full_prompt)
            data = extract_json(response.text)
            
            intent_str = data.get("intent", "CLARIFY").lower()
            confidence = float(data.get("confidence", 0.7))
            
            try:
                intent_type = IntentType(intent_str)
            except ValueError:
                intent_type = IntentType.CLARIFY
                
            return IntentDetection(
                intent=intent_type,
                confidence=confidence,
                hiring_constraints={},
                clarification_needed=[],
                comparison_items=[]
            )
        except Exception as e:
            logger.error(f"Failed to detect intent with LLM: {e}")
            return IntentDetection(intent=IntentType.CLARIFY, confidence=0.5)

    def _extract_constraints(self, messages: List[Message]) -> Dict:
        """Extract constraints using LLM."""
        conversation = "\\n".join([f"{m.role}: {m.content}" for m in messages])
        prompt = build_constraint_extraction_prompt(conversation)
        
        try:
            response = self.llm.generate_content(prompt)
            return extract_json(response.text)
        except Exception as e:
            logger.error(f"Failed to extract constraints: {e}")
            return {}
            
    def _extract_assessment_names(self, user_input: str) -> List[str]:
        """Simple extraction to fallback on or we can use LLM."""
        names = []
        for entry in self.catalog_entries:
            if entry.name.lower() in user_input.lower():
                names.append(entry.name)
        return names
    
    def _handle_clarify(self, user_input: str, intent: IntentDetection, messages: List[Message]) -> ChatResponse:
        """Handle clarification intent."""
        # Retrieve a few general assessments to ground the prompt
        assessments = self.retrieval_service.retrieve(user_input, top_k=3)
        prompt = PromptTemplates.build_clarify_prompt(user_input, assessments)
        
        data = self._generate_json_response(prompt)
        
        return ChatResponse(
            reply=data.get("reply", "Could you provide more details about the role you are hiring for?"),
            recommendations=[],
            end_of_conversation=False
        )
    
    def _handle_recommend(self, user_input: str, intent: IntentDetection, messages: List[Message]) -> ChatResponse:
        """Handle recommendation intent."""
        constraints = self._extract_constraints(messages)
        
        job_role = constraints.get("job_role", user_input)
        job_level = constraints.get("job_level", "unspecified")
        skills = ", ".join(constraints.get("technical_skills", []) + constraints.get("soft_skills", []))
        additional_context = constraints.get("additional_notes", "")
        
        query = f"{job_role} {job_level} {skills} {additional_context}"
        assessments = self.retrieval_service.retrieve(query, top_k=self.settings.retrieval_top_k)
        
        if self.settings.enable_reranking and len(assessments) > self.settings.retrieval_rerank_top_k:
            assessments = self.retrieval_service.rerank_results(
                query,
                assessments,
                top_k=self.settings.retrieval_rerank_top_k
            )
            
        assessments = assessments[:10]
        
        if not assessments:
            return ChatResponse(
                reply="I couldn't find relevant SHL assessments for that query. Could you provide more details?",
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
        
        # Build recommendations list from JSON or just use retrieved items
        recs_data = data.get("recommendations", [])
        recommendations = []
        for r in recs_data:
            if "name" in r and "url" in r:
                recommendations.append(AssessmentRecommendation(
                    name=r["name"],
                    url=r["url"],
                    test_type=r.get("test_type", "general")
                ))
                
        # If the LLM failed to output array, fallback to our retrieval list
        if not recommendations:
            recommendations = [
                AssessmentRecommendation(name=a.name, url=a.url, test_type=a.test_type) 
                for a in assessments
            ]
            
        return ChatResponse(
            reply=data.get("reply", "Here are the recommended assessments."),
            recommendations=recommendations,
            end_of_conversation=False
        )
    
    def _handle_refine(self, user_input: str, intent: IntentDetection, messages: List[Message]) -> ChatResponse:
        """Handle refinement intent."""
        refined_query = f"{' '.join(self.previous_recommendations)} {user_input}"
        updated_assessments = self.retrieval_service.retrieve(refined_query, top_k=10)
        
        prompt = PromptTemplates.build_refine_prompt(
            new_requirement=user_input,
            previous_recommendations=self.previous_recommendations,
            updated_results=updated_assessments
        )
        
        data = self._generate_json_response(prompt)
        
        recs_data = data.get("recommendations", [])
        recommendations = []
        for r in recs_data:
            if "name" in r and "url" in r:
                recommendations.append(AssessmentRecommendation(
                    name=r["name"],
                    url=r["url"],
                    test_type=r.get("test_type", "general")
                ))
                
        if not recommendations:
            recommendations = [
                AssessmentRecommendation(name=a.name, url=a.url, test_type=a.test_type) 
                for a in updated_assessments[:5]
            ]
            
        return ChatResponse(
            reply=data.get("reply", "Here are the updated recommendations based on your new requirement."),
            recommendations=recommendations,
            end_of_conversation=False
        )
    
    def _handle_compare(self, user_input: str, intent: IntentDetection, messages: List[Message]) -> ChatResponse:
        """Handle comparison intent."""
        comparison_items = self._extract_assessment_names(user_input)
        
        matching = []
        for name in comparison_items:
            for entry in self.catalog_entries:
                if name.lower() in entry.name.lower():
                    matching.append(entry)
                    break
        
        # If no specific matches, try to retrieve based on the whole query to find context
        if not matching:
            matching = self.retrieval_service.retrieve(user_input, top_k=3)
            comparison_items = [m.name for m in matching]
            
        if not matching:
            return ChatResponse(
                reply="I couldn't find those specific assessments. Could you provide the exact names from the SHL catalog?",
                recommendations=[],
                end_of_conversation=False
            )
            
        prompt = PromptTemplates.build_compare_prompt(
            assessment_names=comparison_items,
            catalog_entries=matching
        )
        
        data = self._generate_json_response(prompt)
        
        return ChatResponse(
            reply=data.get("reply", "Here is the comparison between the requested assessments."),
            recommendations=[],
            end_of_conversation=False
        )
    
    def _handle_refuse(self, user_input: str, intent: IntentDetection) -> ChatResponse:
        """Handle refusal intent."""
        prompt = PromptTemplates.build_refusal_prompt(topic=user_input)
        
        data = self._generate_json_response(prompt)
        
        return ChatResponse(
            reply=data.get("reply", "I'm specifically designed to recommend SHL assessments. Your question falls outside that scope."),
            recommendations=[],
            end_of_conversation=False
        )
