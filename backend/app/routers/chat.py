from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import StreamingResponse
import logging
from typing import Dict, Any, AsyncGenerator
import json

from app.schemas.chat import (
    ChatMessageRequest,
    ConversationCreate,
    ConversationResponse,
    MessageResponse,
)
from app.middleware.auth import get_user_id
from app.services.db.supabase_client import supabase_client
from app.services.agent.react_agent import react_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    req: Request,
) -> Dict[str, Any]:
    """
    Create a new conversation.
    
    - **title**: Conversation title
    
    Returns the created conversation.
    """
    try:
        user_id = get_user_id(req)
        
        conversation = supabase_client.create_conversation(
            user_id=user_id,
            title=request.title,
        )
        
        logger.info(f"Conversation created: {conversation['id']}")
        
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@router.get("/conversations")
async def list_conversations(req: Request) -> Dict[str, Any]:
    """
    List all conversations for the current user.
    
    Returns a list of conversations.
    """
    try:
        user_id = get_user_id(req)
        
        conversations = supabase_client.get_conversations(user_id)
        
        return {
            "conversations": conversations,
            "count": len(conversations),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations",
        )


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    req: Request,
) -> Dict[str, Any]:
    """
    Get all messages for a conversation.
    
    - **conversation_id**: Conversation ID
    
    Returns a list of messages.
    """
    try:
        user_id = get_user_id(req)
        
        # Verify user owns this conversation
        conversation = supabase_client.get_conversation(
            conversation_id, user_id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        messages = supabase_client.get_messages(
            conversation_id, user_id
        )
        
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "count": len(messages),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages",
        )


@router.post("/message")
async def send_message(
    request: ChatMessageRequest,
    req: Request,
) -> StreamingResponse:
    """
    Send a message and stream the agent response via SSE.
    
    - **conversation_id**: Conversation ID
    - **content**: Message content (max 4096 characters)
    
    Returns Server-Sent Events stream with response tokens.
    """
    try:
        user_id = get_user_id(req)
        request_id = getattr(req.state, "request_id", "unknown")
        
        # Verify conversation exists and belongs to user
        conversation = supabase_client.get_conversation(
            request.conversation_id, user_id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        # Save user message
        supabase_client.save_message(
            conversation_id=request.conversation_id,
            user_id=user_id,
            role="user",
            content=request.content,
        )
        
        logger.info(
            f"[{request_id}] Message received from user {user_id}: {len(request.content)} chars"
        )
        
        # Create SSE stream
        async def event_generator():
            """Generate SSE events."""
            try:
                # Process message with agent
                async for event in react_agent.process_message(
                    request.content,
                    request.conversation_id,
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message",
        )
