"""Chatbot routers for authentication, chat, and health endpoints."""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import StreamingResponse
import logging
from typing import Dict, Any, AsyncGenerator
import json
from datetime import datetime
import uuid

from auth import UnauthorizedError, check_authorization
from supabase_client import supabase_client
from react_agent import react_agent

logger = logging.getLogger(__name__)

# Create routers
auth_router = APIRouter(prefix="/auth", tags=["authentication"])
chat_router = APIRouter(prefix="/chat", tags=["chat"])
health_router = APIRouter(tags=["health"])


# ============================================================================
# Authentication Endpoints
# ============================================================================

@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: Request) -> Dict[str, Any]:
    """Create a new user account."""
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")

        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Email and password required",
            )

        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password must be at least 8 characters",
            )

        result = await supabase_client.create_user(email, password)
        user = result["user"]
        session = result["session"]

        if not session or not session.access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account",
            )

        logger.info(f"User signup successful: {email}")

        return {
            "access_token": session.access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Signup error: {error_msg}")

        if "already registered" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user account",
        )


@auth_router.post("/login")
async def login(request: Request) -> Dict[str, Any]:
    """Authenticate user with email and password."""
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")

        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Email and password required",
            )

        result = await supabase_client.authenticate_user(email, password)
        user = result["user"]
        session = result["session"]

        if not session or not session.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        logger.info(f"User login successful: {email}")

        return {
            "access_token": session.access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


@auth_router.post("/logout", status_code=status.HTTP_200_OK)
async def logout() -> Dict[str, str]:
    """Logout user."""
    logger.info("User logout")
    return {"message": "Logged out successfully"}


# ============================================================================
# Chat Endpoints
# ============================================================================

@chat_router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(request: Request) -> Dict[str, Any]:
    """Create a new conversation."""
    try:
        user_id = check_authorization(request.headers)
        request.state.user_id = user_id
        body = await request.json()
        title = body.get("title", "New Conversation")

        conversation = await supabase_client.create_conversation(user_id, title)
        logger.info(f"Conversation created: {conversation['id']}")

        return conversation
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@chat_router.get("/conversations")
async def list_conversations(request: Request) -> Dict[str, Any]:
    """List all conversations for the current user."""
    try:
        user_id = check_authorization(request.headers)
        request.state.user_id = user_id

        conversations = await supabase_client.get_conversations(user_id)

        return {
            "conversations": conversations,
            "count": len(conversations),
        }
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations",
        )


@chat_router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, request: Request) -> Dict[str, Any]:
    """Get all messages for a conversation."""
    try:
        user_id = check_authorization(request.headers)
        request.state.user_id = user_id

        # Verify user owns this conversation
        conversation = await supabase_client.get_conversation(conversation_id, user_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        messages = await supabase_client.get_messages(conversation_id, user_id)

        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "count": len(messages),
        }
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages",
        )


@chat_router.post("/message")
async def send_message(request: Request) -> StreamingResponse:
    """Send a message and stream the agent response via SSE."""
    try:
        user_id = check_authorization(request.headers)
        request.state.user_id = user_id
        request_id = str(uuid.uuid4())

        body = await request.json()
        conversation_id = body.get("conversation_id")
        content = body.get("content", "").strip()

        if not conversation_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="conversation_id required",
            )

        if not content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="content required",
            )

        if len(content) > 4096:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Message exceeds maximum length (4096 characters)",
            )

        # Verify conversation exists and belongs to user
        conversation = await supabase_client.get_conversation(conversation_id, user_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Save user message
        await supabase_client.save_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=content,
        )

        logger.info(f"[{request_id}] Message received from user {user_id}: {len(content)} chars")

        # Create SSE stream
        async def event_generator() -> AsyncGenerator[str, None]:
            """Generate SSE events."""
            try:
                # Process message with agent
                async for event in react_agent.process_message(
                    content,
                    conversation_id,
                    user_id,
                ):
                    # Format as SSE
                    event_type = event.get("event", "message")
                    event_data = event.get("data", {})

                    sse_line = f"event: {event_type}\n"
                    sse_line += f"data: {json.dumps(event_data)}\n\n"

                    yield sse_line

                    logger.debug(f"[{request_id}] SSE event: {event_type}")

            except Exception as e:
                logger.error(f"[{request_id}] Stream error: {str(e)}")
                error_event = f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                yield error_event

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message",
        )


# ============================================================================
# Health Endpoints
# ============================================================================

@health_router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "backend": "healthy",
            "supabase": "unknown",
            "mcp": "unknown",
        },
    }

    # Check Supabase connectivity
    try:
        await supabase_client.health_check()
        health_status["services"]["supabase"] = "healthy"
    except Exception as e:
        logger.warning(f"Supabase health check failed: {str(e)}")
        health_status["services"]["supabase"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check MCP connectivity
    try:
        is_healthy = await react_agent.health_check()
        health_status["services"]["mcp"] = "healthy" if is_healthy else "unhealthy"
        if not is_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        logger.warning(f"MCP health check failed: {str(e)}")
        health_status["services"]["mcp"] = "unhealthy"
        health_status["status"] = "degraded"

    return health_status


@health_router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint."""
    health_status = await health_check()

    # Check if all services are healthy
    all_healthy = all(
        service_status == "healthy"
        for service_status in health_status["services"].values()
    )

    if not all_healthy:
        return {
            "status": "not_ready",
            "services": health_status["services"],
        }

    return {
        "status": "ready",
        "services": health_status["services"],
    }


@health_router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """Liveness check endpoint."""
    return {"status": "alive"}
