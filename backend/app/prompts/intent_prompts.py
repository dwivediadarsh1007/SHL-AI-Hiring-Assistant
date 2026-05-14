"""
Intent-specific prompt templates.
"""

from typing import List, Dict
from app.models.catalog import CatalogEntry


class IntentPrompts:
    """Intent-specific prompt templates."""
    
    DETECT_INTENT_PROMPT = """Analyze the user's message and determine their intent.

Message: "{user_message}"

Conversation history summary:
{history_summary}

Determine the intent:
1. CLARIFY: User request is vague - need clarifying questions before recommending
2. RECOMMEND: User has provided enough info to recommend assessments
3. REFINE: User is adding new constraints/preferences to existing recommendations
4. COMPARE: User is asking to compare specific assessments
5. REFUSE: Request is off-topic (legal advice, general HR strategy, not about SHL assessments)

Respond with JSON:
{{
  "intent": "CLARIFY|RECOMMEND|REFINE|COMPARE|REFUSE",
  "confidence": 0.95,
  "reasoning": "Brief explanation of why you chose this intent"
}}
"""
    
    EXTRACT_CONSTRAINTS_PROMPT = """Extract hiring constraints from the conversation.

Conversation:
{conversation}

Extract and structure:
{{
  "job_role": "specific job title or description",
  "job_level": "junior|mid|senior|executive",
  "technical_skills": ["skill1", "skill2"],
  "soft_skills": ["skill1", "skill2"],
  "industry": "if mentioned",
  "team_size": "if relevant",
  "assessment_preferences": "speed, depth, or balanced",
  "additional_notes": "any other relevant context"
}}

Only include fields where user provided explicit information.
"""
    
    EXTRACT_COMPARISON_ITEMS_PROMPT = """Extract assessment names to compare from the user message.

Message: "{user_message}"

Available assessments in catalog:
{available_assessments}

Return JSON:
{{
  "requested_assessments": ["Name1", "Name2"],
  "matched_in_catalog": true|false,
  "notes": "if any assessment name was ambiguous or not found"
}}
"""
    
    VALIDATE_RESPONSE_PROMPT = """Validate that the response is grounded in the provided SHL catalog.

Response to validate:
{response}

SHL Catalog:
{catalog_info}

Check:
1. Are all assessment names real (from catalog)?
2. Are all URLs from the catalog?
3. Are descriptions accurate to the catalog?
4. No hallucinated assessments?
5. Valid JSON format?

Respond with:
{{
  "valid": true|false,
  "issues": ["list of issues if any"],
  "corrected_response": "corrected response if needed"
}}
"""


class ComparisonPrompts:
    """Specialized prompts for assessment comparison."""
    
    COMPARISON_STRUCTURE_PROMPT = """Create a structured comparison of these SHL assessments:

Assessments to compare:
{assessment_names}

Catalog information:
{catalog_info}

Provide:
1. **Overview Table**
   - Measurement Focus
   - Typical Duration
   - Best For (job types)

2. **Detailed Differences**
   - What each measures specifically
   - Unique strengths

3. **Combination Recommendations**
   - Which assessments complement each other
   - Why use together vs. separately

4. **Selection Decision Matrix**
   - When to use Assessment A vs. B vs. C
   - Based on: job level, role type, assessment depth needed

Keep recruiter-friendly and concise.
"""


class ClarificationPrompts:
    """Specialized prompts for clarification flows."""
    
    ASK_FOLLOWUP_PROMPT = """Generate a helpful follow-up question to clarify the hiring requirement.

Current understanding:
{current_context}

Missing information:
- Job level (junior/mid/senior/exec)?
- Role type (technical/leadership/customer-facing)?
- Team dynamics?
- Urgency/assessment speed needs?

Ask ONE clear, specific question that helps narrow down the right assessments.
The question should be answerable and guide toward SHL assessment selection.

Question:
"""
    
    CLARIFICATION_FLOW_PROMPT = """Provide clarification guidance.

User requirement: "{requirement}"
Clarifications asked: {clarifications_asked}
Remaining ambiguity: {ambiguity}

Decide:
1. Can we recommend now with reasonable confidence?
2. Or need more specific information?

If can recommend: Proceed with recommendation prompt
If need more info: Ask specific follow-up question (max 2 questions)

Current status:
"""


class RefinementPrompts:
    """Specialized prompts for recommendation refinement."""
    
    REFINE_FLOW_PROMPT = """Handle a refinement request.

Previous recommendations:
{previous}

New user request: "{new_request}"

Determine:
1. Does the new request add constraints (more restrictive)?
2. Does it add requirements (additional needs)?
3. Does it contradict previous info?

Action:
- If additive: Add complementary assessments or reorder
- If restrictive: Replace recommendations with better fit
- If contradictory: Clarify with user

Updated recommendations should still be from the catalog.
"""


class RefusalPrompts:
    """Specialized prompts for refusal handling."""
    
    CLASSIFY_OFF_TOPIC_PROMPT = """Classify the off-topic request.

User message: "{message}"

Categories:
1. LEGAL_ADVICE - asking about employment law, contracts, regulations
2. GENERAL_HR_STRATEGY - broad hiring strategy, not assessment-specific
3. COMPETITOR_INFO - asking about other vendors' assessments
4. IMPLEMENTATION_HELP - how to run assessments, administration
5. RESULTS_INTERPRETATION - how to interpret assessment scores/results
6. COMPLETELY_UNRELATED - totally off-topic

Classification: [CATEGORY]
Recommended response: [polite refusal with redirect to SHL assessments]
"""


def build_intent_detection_prompt(user_message: str, history_summary: str) -> str:
    """Build intent detection prompt."""
    return IntentPrompts.DETECT_INTENT_PROMPT.format(
        user_message=user_message,
        history_summary=history_summary
    )


def build_constraint_extraction_prompt(conversation: str) -> str:
    """Build constraint extraction prompt."""
    return IntentPrompts.EXTRACT_CONSTRAINTS_PROMPT.format(
        conversation=conversation
    )


def build_comparison_prompt(
    assessment_names: List[str],
    catalog_info: str
) -> str:
    """Build assessment comparison prompt."""
    names = ", ".join(assessment_names)
    return ComparisonPrompts.COMPARISON_STRUCTURE_PROMPT.format(
        assessment_names=names,
        catalog_info=catalog_info
    )
