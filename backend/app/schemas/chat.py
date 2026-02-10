from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message."""
    conversation_id: str = Field(..., description="Conversation ID")
    content: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Message content (max 4096 characters)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "content": "What are the latest trends in AI?"
            }
        }


class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""
    title: str = Field(..., min_length=1, max_length=255, description="Conversation title")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "AI Trends Discussion"
            }
        }


class MessageResponse(BaseModel):
    """Response model for a message."""
    id: str
    conversation_id: str
    user_id: str
    role: str
    content: str
    tool_calls: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Response model for a conversation."""
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """Response model for a conversation with messages."""
    messages: List[MessageResponse] = []


class ChatStreamEvent(BaseModel):
    """Base model for SSE events."""
    event: str
    data: Dict[str, Any]


class TokenEvent(BaseModel):
    """SSE event for token streaming."""
    token: str


class ToolActivityEvent(BaseModel):
    """SSE event for tool activity."""
    tool: str
    status: str  # 'started', 'completed', 'failed'
    error: Optional[str] = None


class DoneEvent(BaseModel):
    """SSE event for completion."""
    message_id: str
