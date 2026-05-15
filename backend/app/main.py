"""
SHL Assessment Recommender - FastAPI Application
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models.api import HealthResponse, ChatRequest, ChatResponse
from app.utils.config import get_settings
from app.agents.dialog_manager import DialogManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Global dialog manager instance
dialog_manager: DialogManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for app startup and shutdown."""
    global dialog_manager
    
    # Startup
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    
    try:
        # Initialize dialog manager
        dialog_manager = DialogManager()
        logger.info("✓ Dialog manager initialized")
        
        # Load or build FAISS index
        if dialog_manager.retrieval_service.load_index():
            logger.info("✓ Loaded existing FAISS index")
        else:
            logger.warning("No existing FAISS index found, building from catalog...")
            if dialog_manager.retrieval_service.build_index(dialog_manager.catalog_entries):
                logger.info("✓ Built and saved FAISS index")
            else:
                logger.warning("⚠ Failed to build FAISS index (retrieval may be limited)")
    
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        dialog_manager = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down SHL Assessment Recommender")


# Create FastAPI app instance
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Conversational AI agent for SHL assessment recommendations",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check endpoint"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthResponse with status 'ok'
    """
    return HealthResponse(status="ok")


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["chat"],
    summary="Conversational chat endpoint",
    responses={
        200: {
            "description": "Successful response",
            "model": ChatResponse
        },
        400: {
            "description": "Invalid request format"
        },
        422: {
            "description": "Validation error"
        },
        503: {
            "description": "Service not ready"
        }
    }
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint for conversational assessment recommendations.
    
    This endpoint:
    1. Validates the conversation history
    2. Detects user intent (clarify, recommend, refine, compare, refuse)
    3. Retrieves relevant SHL assessments
    4. Generates a grounded, catalog-backed response
    5. Validates all outputs against guardrails
    
    Args:
        request: ChatRequest containing conversation history
        - messages: List of Message objects with role ('user' or 'assistant') and content
        
    Returns:
        ChatResponse with:
        - reply: Conversational text response
        - recommendations: List of recommended SHL assessments (max 10)
        - end_of_conversation: Flag indicating if conversation should end
        
    Raises:
        HTTPException: If request validation fails or service unavailable
    """
    try:
        # Check if dialog manager is initialized
        if dialog_manager is None:
            logger.error("Dialog manager not initialized")
            raise HTTPException(
                status_code=503,
                detail="Service not ready. Please try again later."
            )
        
        # Validate request
        if not request.messages or len(request.messages) == 0:
            raise HTTPException(
                status_code=400,
                detail="At least one message is required"
            )
        
        # Ensure last message is from user
        if request.messages[-1].role != "user":
            raise HTTPException(
                status_code=400,
                detail="Last message must be from user"
            )
        
        # Process message through dialog manager
        logger.info(f"Processing chat request with {len(request.messages)} messages")
        
        response = dialog_manager.process_message(request.messages)
        
        # Validate response through guardrails
        is_valid, validated_response, errors = dialog_manager.guardrail_manager.validate_agent_response(
            {
                "reply": response.reply,
                "recommendations": [
                    {
                        "name": r.name,
                        "url": r.url,
                        "test_type": r.test_type
                    }
                    for r in response.recommendations
                ],
                "end_of_conversation": response.end_of_conversation
            }
        )
        
        if not is_valid:
            logger.warning(f"Response validation errors: {errors}")
            # Return validated response with corrections
            if validated_response:
                response = validated_response
        
        logger.info(f"Chat response generated: {len(response.recommendations)} recommendations")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request."
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
