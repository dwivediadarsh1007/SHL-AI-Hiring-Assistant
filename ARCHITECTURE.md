"""
Project structure and layout documentation.
"""

# SHL Assessment Recommender - Project Structure

## Directory Layout

```
project/
│
├── app/                           # Main application package
│   ├── main.py                   # FastAPI application entry point
│   ├── routes/                   # API route handlers
│   │   └── chat.py               # Chat endpoint
│   ├── services/                 # Business logic services
│   │   ├── catalog_service.py    # Catalog loading and access
│   │   ├── embedding_service.py  # Text embedding pipeline
│   │   ├── retrieval_service.py  # Semantic search orchestration
│   │   └── scraper.py            # SHL catalog scraper
│   ├── prompts/                  # LLM prompt templates
│   │   ├── base_prompts.py       # Core system and task prompts
│   │   └── intent_prompts.py     # Intent-specific prompts
│   ├── models/                   # Data models and schemas
│   │   ├── api.py                # Pydantic API schemas
│   │   ├── catalog.py            # Catalog entry models
│   │   └── intents.py            # Intent classification models
│   ├── utils/                    # Utilities
│   │   ├── config.py             # Configuration management
│   │   └── validation.py         # Input validation
│   ├── retrieval/                # Semantic search
│   │   └── faiss_index.py        # FAISS indexing and search
│   ├── agents/                   # Dialog orchestration
│   │   └── dialog_manager.py     # Main conversation controller
│   └── guards/                   # Safety and validation
│       └── guardrail.py          # Hallucination, injection, schema guards
│
├── data/                         # Data files
│   └── shl_catalog.json          # SHL assessment catalog
│
├── vectorstore/                  # Vector index storage
│   ├── shl_index.faiss           # FAISS index (built at runtime)
│   └── metadata.json             # Index metadata
│
├── scripts/                      # Utility scripts
│   ├── scrape_shl_catalog.py     # Download/update catalog
│   ├── build_faiss_index.py      # Build vector index
│   └── validate_catalog.py       # Validate catalog integrity
│
├── tests/                        # Test suite
│   ├── test_api.py               # API integration tests
│   ├── test_catalog.py           # Catalog and scraper tests
│   ├── test_retrieval.py         # Embedding and retrieval tests
│   ├── test_guardrails.py        # Guardrail validation tests
│   └── test_schema.py            # Pydantic schema tests
│
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables template
├── README.md                     # Project documentation
├── render.yaml                   # Render deployment config
├── railway.toml                  # Railway deployment config
├── Dockerfile                    # Container configuration
├── start.sh                      # Unix startup script
├── start.bat                     # Windows startup script
└── .gitignore                    # Git ignore rules
```

## Module Responsibilities

### Services (`app/services/`)
- **catalog_service.py**: Loads and caches SHL catalog in memory
- **embedding_service.py**: Generates embeddings using sentence-transformers
- **retrieval_service.py**: Orchestrates semantic search (FAISS + reranking)
- **scraper.py**: Downloads and parses SHL assessment data

### Retrieval (`app/retrieval/`)
- **faiss_index.py**: FAISS index management with fallback in-memory store

### Agents (`app/agents/`)
- **dialog_manager.py**: Main conversation controller (intent detection → retrieval → response)

### Guards (`app/guards/`)
- **guardrail.py**: Prevents hallucination, prompt injection, schema violations, invalid URLs

### Prompts (`app/prompts/`)
- **base_prompts.py**: System prompts, task-specific templates
- **intent_prompts.py**: Intent detection, constraint extraction, comparison guidance

### Models (`app/models/`)
- **api.py**: Pydantic request/response schemas (ChatRequest, ChatResponse, Message)
- **catalog.py**: CatalogEntry and metadata models
- **intents.py**: IntentType enum and IntentDetection model

### Utils (`app/utils/`)
- **config.py**: Environment-based configuration with defaults
- **validation.py**: URL validation, injection detection, input sanitization

## Data Flow

```
User Message
    ↓
[API] POST /chat
    ↓
ChatRequest Validation (Pydantic)
    ↓
DialogManager.process_message()
    ↓
[1] Detect Intent (CLARIFY | RECOMMEND | REFINE | COMPARE | REFUSE)
    ↓
[2] Extract Constraints from conversation history
    ↓
[3] RetrievalService.retrieve() for semantic search
    │   ├── EmbeddingService.encode_query()
    │   ├── FAISSIndex.search()
    │   └── Rerank if enabled
    ↓
[4] Generate LLM Prompt (using PromptTemplates)
    ↓
[5] GuardrailManager validation
    │   ├── HallucinationGuard
    │   ├── PromptInjectionGuard
    │   ├── SchemaGuard
    │   └── URLGuard
    ↓
ChatResponse
    ↓
[API] JSON Response
```

## Key Design Decisions

1. **Stateless API**: All conversation history passed in each request
2. **Grounded Generation**: Only real SHL catalog assessments returned
3. **Layered Guardrails**: Multiple validation layers before response
4. **Modular Architecture**: Clear separation between retrieval, orchestration, and responses
5. **Lazy Loading**: Models and indexes loaded on first use
6. **Fallback Mechanisms**: In-memory search if FAISS unavailable

## Extension Points

1. **New Intent Types**: Add to `IntentType` enum and `DialogManager._detect_intent()`
2. **Custom Prompts**: Add templates to `app/prompts/`
3. **Additional Guardrails**: Implement in `app/guards/guardrail.py`
4. **Retrieval Methods**: Extend `HybridRetriever` for different search strategies
5. **LLM Providers**: Replace Gemini with other providers in dialog manager
