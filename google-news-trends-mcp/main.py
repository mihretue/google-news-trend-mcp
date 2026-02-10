from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import logging

from mcp_server import mcp_http_app
from chatbot_routers import auth_router, chat_router, health_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Google News Trends MCP + Chatbot",
    description="MCP server with integrated chatbot for news and trends",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount MCP server
app.mount("/mcp", mcp_http_app)

# Include chatbot routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(health_router)


@app.get("/healthz")
async def healthz() -> PlainTextResponse:
    return PlainTextResponse("ok")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Google News Trends MCP + Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "mcp": "/mcp",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
