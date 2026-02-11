from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uuid
from datetime import datetime

from app.core.config import settings
from app.middleware.auth import AuthMiddleware
from app.routers import auth, health, chat

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LangChain ReAct Chatbot",
    description="A full-stack LangChain ReAct chatbot with streaming responses",
    version="1.0.0",
)

# Add authentication middleware (must be added BEFORE CORS so it runs after CORS)
app.add_middleware(AuthMiddleware)

# Configure CORS (added after auth so it runs first in the middleware stack)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Duration: {process_time:.3f}s"
    )
    
    response.headers["X-Request-ID"] = request_id
    return response


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("=" * 50)
    logger.info("Starting LangChain ReAct Chatbot")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"MCP URL: {settings.mcp_url}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down LangChain ReAct Chatbot")


# Include routers
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LangChain ReAct Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "environment": settings.environment,
    }
