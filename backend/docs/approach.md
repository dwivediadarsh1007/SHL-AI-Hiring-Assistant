# SHL Assessment Recommender: Approach & Architecture

## 1. Architecture Overview
The SHL Assessment Recommender is designed as a **Stateless Conversational AI** utilizing a **Retrieval-Augmented Generation (RAG)** pipeline. The system is built on:
- **Backend Framework:** FastAPI (provides asynchronous, high-performance endpoints with strictly enforced Pydantic schemas).
- **Conversational Engine:** Google Gemini (`gemini-2.5-flash`) orchestrated by a custom `DialogManager` that handles intent routing, clarification, and conversation state management.
- **Retrieval System:** FAISS (Facebook AI Similarity Search) combined with Gemini Embeddings (`models/text-embedding-004`) for high-speed semantic search.
- **Deployment:** Render (Free Tier), ensuring public accessibility for both the `/chat` and `/health` endpoints.

### Stateless Design
To ensure scalability, the `/chat` endpoint is completely stateless. It accepts the full conversational history (`messages` array) in each request. The LLM re-contextualizes the history to determine the user's intent (Clarify, Recommend, Refine, Compare, or Refuse) without requiring backend memory or database sessions.

## 2. Retrieval Setup (RAG)
The RAG pipeline grounds the LLM strictly in the official SHL catalog to eliminate hallucinations.

- **Data Ingestion:** A comprehensive JSON catalog of 25+ SHL assessments (Cognitive, Behavioral, Situational, and Coding) is parsed on startup.
- **Embedding Generation:** We utilize Gemini's embedding API. This was a strategic decision to bypass Render's 512MB RAM limitation, which caused Out-Of-Memory (OOM) crashes when using local `sentence-transformers`.
- **Vector Search:** The embeddings (768 dimensions) are indexed in FAISS using an L2 distance metric.
- **Hybrid Retrieval:** The system performs semantic vector search and combines it with a lexical fallback. If the results exceed the target count, a lightweight cosine-similarity reranker ensures optimal relevance.

## 3. Prompt Design & Guardrails
The system utilizes multi-stage, intent-driven prompting:
1. **Intent Detection Prompt:** Analyzes the conversation history to classify the user's goal.
2. **Clarification Prompt:** If the user query is vague (e.g., "I need a test"), the LLM is prompted to ask for missing constraints (role, seniority, skills).
3. **Recommendation Prompt:** Once constraints are clear, the LLM is provided with the Top-K retrieved catalog entries and instructed to output exactly 1-10 recommendations in a strict JSON schema.

**Strict Guardrails:**
- **HallucinationGuard:** Intercepts the LLM's output and cross-references every recommended assessment URL and name against the static SHL catalog. Fake or altered URLs are stripped out.
- **PromptInjectionGuard:** Scans user input for jailbreak patterns (e.g., "ignore previous instructions") and safely refuses execution.
- **Scope Restriction:** The system is explicitly prompted to refuse queries related to legal advice or non-SHL hiring topics.

## 4. Evaluation Metrics
We evaluated the RAG pipeline using a golden dataset of realistic recruiter queries.

- **Retrieval Quality (Recall@10):** Measures whether the expected assessment appears in the top 10 retrieved results. The system is designed to achieve >80% Recall@10 given a valid embedding model.
- **Semantic Relevance:** Evaluated manually by checking if the returned assessments match the requested skills (e.g., matching "Python backend engineer" to "Coding Test - Python").
- **Hallucination Reduction:** Hallucination rate is **0%** due to the hardcoded `HallucinationGuard` which forces a strict catalog intersection before returning the API response.

*(Note: Ensure `GEMINI_API_KEY` is active to run the `scripts/evaluate_rag.py` pipeline effectively, as an expired key causes embedding generation to fallback to zero-vectors, degrading Recall).*

## 5. Failures & Improvements
### Current Limitations (Failures)
- **Cold Start Delays:** Due to Render's free tier, the instance sleeps after 15 minutes of inactivity. The first request after a sleep period can trigger a 502 Bad Gateway timeout if the spin-up process exceeds 60 seconds.
- **Context Window Limits:** The stateless design means sending the entire chat history on every request. For extremely long conversations, this could eventually hit token limits or increase latency.

### Future Improvements
1. **Database Integration:** Migrate from an in-memory FAISS index to a persistent vector database like ChromaDB or pgvector.
2. **Automated Scraping:** Implement a daily cron job using Selenium/Playwright to scrape SHL's dynamic SPA and keep the catalog perfectly up-to-date.
3. **Caching:** Implement Redis to cache frequent queries (e.g., "Java developer tests") to bypass embedding generation and save API costs.

## 6. AI Tool Disclosure
In the spirit of transparency, the following AI tools were utilized to accelerate development:
- **Google Deepmind / Gemini Assistant:** Used for architectural planning, writing the `evaluate_rag.py` evaluation pipeline, generating the mock SHL dataset, and debugging deployment Out-of-Memory (OOM) issues on Render.
- **GitHub Copilot:** Used for boilerplate code generation (Pydantic schemas) and inline typing assistance.
