"""
Integration tests for end-to-end chat flow.
Tests: sending message → agent response → message saved → chat history restoration
"""
import pytest
import httpx
import asyncio
import json
from typing import Dict, Any

# Backend API base URL
BASE_URL = "http://localhost:8000"

# Test user credentials
TEST_EMAIL = "chat_integration_test@example.com"
TEST_PASSWORD = "TestPassword123!"


class TestChatFlow:
    """Test end-to-end chat flow."""

    @pytest.fixture
    async def client(self):
        """Create HTTP client for testing."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
            yield client

    @pytest.fixture
    async def authenticated_client(self, client):
        """Create authenticated HTTP client."""
        # Signup
        response = await client.post(
            "/auth/signup",
            json={
                "email": f"chat_test_{asyncio.get_event_loop().time()}@example.com",
                "password": TEST_PASSWORD,
            },
        )
        assert response.status_code == 201
        token = response.json()["access_token"]
        
        # Add token to client headers
        client.headers.update({"Authorization": f"Bearer {token}"})
        yield client

    @pytest.mark.asyncio
    async def test_create_conversation(self, authenticated_client):
        """Test creating a new conversation."""
        response = await authenticated_client.post(
            "/chat/conversations",
            json={"title": "Test Conversation"},
        )
        
        assert response.status_code == 200, f"Create conversation failed: {response.text}"
        data = response.json()
        
        assert "id" in data, "No conversation ID in response"
        assert data["title"] == "Test Conversation", "Title mismatch"
        assert "user_id" in data, "No user_id in response"

    @pytest.mark.asyncio
    async def test_list_conversations(self, authenticated_client):
        """Test listing user's conversations."""
        # Create a conversation first
        create_response = await authenticated_client.post(
            "/chat/conversations",
            json={"title": "Test Conversation"},
        )
        assert create_response.status_code == 200
        
        # List conversations
        response = await authenticated_client.get("/chat/conversations")
        
        assert response.status_code == 200, f"List conversations failed: {response.text}"
        data = response.json()
        
        assert "conversations" in data, "No conversations in response"
        assert "count" in data, "No count in response"
        assert data["count"] >= 1, "Should have at least one conversation"

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, authenticated_client):
        """Test retrieving messages for a conversation."""
        # Create a conversation
        create_response = await authenticated_client.post(
            "/chat/conversations",
            json={"title": "Test Conversation"},
        )
        assert create_response.status_code == 200
        conversation_id = create_response.json()["id"]
        
        # Get messages
        response = await authenticated_client.get(
            f"/chat/conversations/{conversation_id}/messages"
        )
        
        assert response.status_code == 200, f"Get messages failed: {response.text}"
        data = response.json()
        
        assert "messages" in data, "No messages in response"
        assert "count" in data, "No count in response"
        assert data["conversation_id"] == conversation_id, "Conversation ID mismatch"

    @pytest.mark.asyncio
    async def test_send_message_and_receive_response(self, authenticated_client):
        """Test sending a message and receiving agent response via SSE."""
        # Create a conversation
        create_response = await authenticated_client.post(
            "/chat/conversations",
            json={"title": "Test Conversation"},
        )
        assert create_response.status_code == 200
        conversation_id = create_response.json()["id"]
        
        # Send a message
        response = await authenticated_client.post(
            "/chat/message",
            json={
                "conversation_id": conversation_id,
                "content": "What is 2+2?",
            },
        )
        
        assert response.status_code == 200, f"Send message failed: {response.text}"
        
        # Parse SSE stream
        events = []
        for line in response.text.split("\n"):
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
                events.append(event_type)
        
        # Should have at least some events
        assert len(events) > 0, "No SSE events received"

    @pytest.mark.asyncio
    async def test_message_saved_to_database(self, authenticated_client):
        """Test that sent messages are saved to database."""
        # Create a conversation
        create_response = await authenticated_client.post(
            "/chat/conversations",
            json={"title": "Test Conversation"},
        )
        assert create_response.status_code == 200
        conversation_id = create_response.json()["id"]
        
        # Send a message
        message_content = "Test message for database"
        response = await authenticated_client.post(
            "/chat/message",
            json={
                "conversation_id": conversation_id,
                "content": message_content,
            },
        )
        assert response.status_code == 200
        
        # Retrieve messages
        messages_response = await authenticated_client.get(
            f"/chat/conversations/{conversation_id}/messages"
        )
        assert messages_response.status_code == 200
        messages = messages_response.json()["messages"]
        
        # Find the sent message
        user_messages = [m for m in messages if m.get("role") == "user"]
        assert len(user_messages) > 0, "User message not found in database"
        assert user_messages[0]["content"] == message_content, "Message content mismatch"

    @pytest.mark.asyncio
    async def test_chat_history_restoration(self, authenticated_client):
        """Test that chat history is restored correctly."""
        # Create a conversation
        create_response = await authenticated_client.post(
            "/chat/conversations",
            json={"title": "History Test"},
        )
        assert create_response.status_code == 200
        conversation_id = create_response.json()["id"]
        
        # Send multiple messages
        messages = ["First message", "Second message", "Third message"]
        for msg in messages:
            response = await authenticated_client.post(
                "/chat/message",
                json={
                    "conversation_id": conversation_id,
                    "content": msg,
                },
            )
            assert response.status_code == 200
        
        # Retrieve all messages
        messages_response = await authenticated_client.get(
            f"/chat/conversations/{conversation_id}/messages"
        )
        assert messages_response.status_code == 200
        retrieved_messages = messages_response.json()["messages"]
        
        # Verify all messages are present
        user_messages = [m for m in retrieved_messages if m.get("role") == "user"]
        assert len(user_messages) >= len(messages), "Not all messages retrieved"

    @pytest.mark.asyncio
    async def test_unauthorized_access_to_other_users_conversation(self, client):
        """Test that users cannot access other users' conversations."""
        # Create first user and conversation
        user1_response = await client.post(
            "/auth/signup",
            json={
                "email": f"user1_{asyncio.get_event_loop().time()}@example.com",
                "password": TEST_PASSWORD,
            },
        )
        assert user1_response.status_code == 201
        user1_token = user1_response.json()["access_token"]
        user1_id = user1_response.json()["user_id"]
        
        # Create conversation as user1
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        conv_response = await client.post(
            "/chat/conversations",
            json={"title": "User1 Conversation"},
            headers=user1_headers,
        )
        assert conv_response.status_code == 200
        conversation_id = conv_response.json()["id"]
        
        # Create second user
        user2_response = await client.post(
            "/auth/signup",
            json={
                "email": f"user2_{asyncio.get_event_loop().time()}@example.com",
                "password": TEST_PASSWORD,
            },
        )
        assert user2_response.status_code == 201
        user2_token = user2_response.json()["access_token"]
        
        # Try to access user1's conversation as user2
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        response = await client.get(
            f"/chat/conversations/{conversation_id}/messages",
            headers=user2_headers,
        )
        
        # Should be forbidden or not found
        assert response.status_code in [403, 404], f"Expected 403 or 404, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
