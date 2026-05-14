"""
Base prompt templates for LLM interactions.

All prompts are grounded in SHL catalog and designed for concise recruiter-friendly responses.
"""

from typing import List
from app.models.catalog import CatalogEntry


class PromptTemplates:
    """Collection of system and task prompts."""
    
    # ==================== SYSTEM PROMPTS ====================
    
    SYSTEM_PROMPT = """You are an expert SHL assessment recommender assistant helping recruiters and hiring managers discover appropriate assessments.

Your role:
- Help clarify vague hiring requirements through focused questions
- Recommend relevant SHL assessments based on specific job requirements
- Explain differences between assessments
- Refuse out-of-scope requests (legal advice, general hiring strategy, etc.)
- ALWAYS use only the provided SHL catalog - NEVER invent assessments or URLs

Key principles:
1. Be concise and recruiter-friendly (target audience is busy hiring managers)
2. Ask clarifying questions one or two at a time when requirements are vague
3. Provide specific assessment recommendations with clear reasoning
4. Always include assessment URLs when recommending
5. Maximum recommendations: 10 per response
6. If user asks about assessments outside SHL scope, politely decline

Tone: Professional, helpful, authoritative."""

    SAFETY_GUARDRAIL = """CRITICAL GUARDRAILS:
- NEVER recommend assessments not in the provided catalog
- NEVER invent URLs or assessment names
- NEVER provide legal advice, HR policies, or general hiring strategy
- NEVER hallucinate details about assessments not in the catalog
- If uncertain about an assessment, ask for clarification or decline

If asked something outside SHL assessments, respond: "I'm specifically designed to help with SHL assessments. Your question falls outside that scope. Is there an SHL assessment recommendation I can help with?"
"""
    
    # ==================== CLARIFICATION PROMPTS ====================
    
    CLARIFY_PROMPT_TEMPLATE = """Based on the hiring requirement: "{requirement}"

You need to ask clarifying questions to recommend appropriate assessments.

Ask 1-2 focused questions to understand:
- Job level (junior, mid, senior, C-level)
- Role type (technical, leadership, customer-facing, analytical)
- Key skills needed
- Assessment preferences (speed vs. depth)

Keep questions brief and actionable. After the user provides more info, you will recommend specific SHL assessments.

Provided SHL Catalog:
{catalog_info}

Respond with:
1. A brief acknowledgment of their need
2. Specific clarification questions (2-3 max)
3. Optional: "Once you clarify, I can recommend specific SHL assessments that match your needs."
"""
    
    # ==================== RECOMMENDATION PROMPTS ====================
    
    RECOMMEND_PROMPT_TEMPLATE = """Based on the hiring requirements:
- Job: {job_description}
- Level: {job_level}
- Key Skills: {skills}
{additional_context}

Recommend the most relevant SHL assessments from this catalog:
{catalog_info}

Instructions:
1. Recommend 3-7 assessments maximum
2. For each assessment, explain WHY it's relevant to this specific role
3. Include the assessment name, type, and expected duration
4. ONLY recommend assessments from the provided catalog
5. Group recommendations by purpose (e.g., "Core Technical Skills", "Behavioral Assessment")
6. Keep explanations 1-2 sentences each

Format each recommendation as:
- **[Assessment Name]** ([Type], [Duration])
  Why it's relevant: [Brief explanation specific to the job]

End with: "These assessments will give you comprehensive insight into [candidate capability summary]."
"""
    
    # ==================== COMPARISON PROMPTS ====================
    
    COMPARE_PROMPT_TEMPLATE = """Compare the following SHL assessments:
{assessment_names}

Provide:
1. **Key Differences**: What each assessment measures
2. **When to Use Each**: Specific scenarios and job types
3. **Strengths & Limitations**: What you'll learn vs. what you won't
4. **Recommended Combinations**: Which assessments complement each other

Use ONLY information from the catalog below:
{catalog_info}

Keep explanations concise and recruiter-focused.
"""
    
    # ==================== REFUSAL PROMPTS ====================
    
    REFUSE_PROMPT = """I appreciate your question, but this falls outside my area of expertise. I'm specifically designed to recommend SHL assessments.

Your question about "{topic}" is not related to SHL assessment selection.

I can help you with:
- Recommending relevant SHL assessments for specific roles
- Explaining differences between SHL tests
- Clarifying which assessments measure specific competencies

Is there an SHL assessment selection I can help you with?"""
    
    # ==================== REFINEMENT PROMPTS ====================
    
    REFINE_PROMPT_TEMPLATE = """The user provided new context: "{new_requirement}"

Previous recommendations were:
{previous_recommendations}

Using the refined requirement and conversation history, determine if you should:
1. Keep the previous recommendations as-is
2. Add new complementary assessments
3. Replace some recommendations with better-fit assessments

New SHL Catalog Search:
{updated_search_results}

Provide an updated recommendation response acknowledging the new requirement and explaining any changes to the assessment list.
"""
    
    # ==================== JSON FORMATTING ====================
    
    JSON_FORMAT_INSTRUCTION = """Your response MUST be valid JSON matching this schema:
{
  "reply": "Your conversational response to the user",
  "recommendations": [
    {
      "name": "Assessment Name",
      "url": "https://www.shl.com/...",
      "test_type": "cognitive|personality|situational|ability|language|technical"
    }
  ],
  "end_of_conversation": false
}

CRITICAL:
- "reply" must be a single string (no newlines in JSON string - use \\n if needed)
- "recommendations" must be an array (can be empty [])
- "end_of_conversation" is true only when user explicitly wants to end or conversation limit reached
- All URLs must start with https://www.shl.com
- test_type must be one of the predefined values
- Ensure valid JSON - no trailing commas, proper escaping
"""
    
    # ==================== PROMPT BUILDING METHODS ====================
    
    @staticmethod
    def build_clarify_prompt(requirement: str, catalog_entries: List[CatalogEntry]) -> str:
        """Build clarification prompt."""
        catalog_info = PromptTemplates._format_catalog(catalog_entries)
        
        return PromptTemplates.CLARIFY_PROMPT_TEMPLATE.format(
            requirement=requirement,
            catalog_info=catalog_info
        )
    
    @staticmethod
    def build_recommend_prompt(
        job_description: str,
        job_level: str,
        skills: str,
        additional_context: str,
        catalog_entries: List[CatalogEntry]
    ) -> str:
        """Build recommendation prompt."""
        catalog_info = PromptTemplates._format_catalog(catalog_entries)
        additional = f"\n- Additional Info: {additional_context}" if additional_context else ""
        
        return PromptTemplates.RECOMMEND_PROMPT_TEMPLATE.format(
            job_description=job_description,
            job_level=job_level,
            skills=skills,
            additional_context=additional,
            catalog_info=catalog_info
        )
    
    @staticmethod
    def build_compare_prompt(
        assessment_names: List[str],
        catalog_entries: List[CatalogEntry]
    ) -> str:
        """Build comparison prompt."""
        catalog_info = PromptTemplates._format_catalog(catalog_entries)
        names_str = ", ".join(assessment_names)
        
        return PromptTemplates.COMPARE_PROMPT_TEMPLATE.format(
            assessment_names=names_str,
            catalog_info=catalog_info
        )
    
    @staticmethod
    def build_refusal_prompt(topic: str) -> str:
        """Build refusal response."""
        return PromptTemplates.REFUSE_PROMPT.format(topic=topic)
    
    @staticmethod
    def build_refine_prompt(
        new_requirement: str,
        previous_recommendations: List[str],
        updated_results: List[CatalogEntry]
    ) -> str:
        """Build refinement prompt."""
        prev_recs = ", ".join(previous_recommendations) if previous_recommendations else "None"
        updated_search = PromptTemplates._format_catalog(updated_results)
        
        return PromptTemplates.REFINE_PROMPT_TEMPLATE.format(
            new_requirement=new_requirement,
            previous_recommendations=prev_recs,
            updated_search_results=updated_search
        )
    
    @staticmethod
    def _format_catalog(entries: List[CatalogEntry]) -> str:
        """Format catalog entries for inclusion in prompts."""
        if not entries:
            return "No assessments available."
        
        formatted = []
        for entry in entries:
            formatted.append(
                f"- **{entry.name}** ({entry.test_type}, {entry.duration})\n"
                f"  Description: {entry.description}\n"
                f"  Skills: {entry.skills}\n"
                f"  URL: {entry.url}"
            )
        
        return "\n\n".join(formatted)
    
    @staticmethod
    def build_system_prompt_with_guardrails() -> str:
        """Build complete system prompt with safety guardrails."""
        return PromptTemplates.SYSTEM_PROMPT + "\n\n" + PromptTemplates.SAFETY_GUARDRAIL
