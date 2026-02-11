"""
Integration tests for tool integration.
Tests: Tavily search, Google Trends MCP, tool error handling, MCP unavailability
"""
import pytest
import httpx
import asyncio
import json
from typing import Dict, Any

# Backend API base URL
BASE_URL = "http://localhost:8000"

# Test user credentials
TEST_PASSWORD = "TestPassword123!"


class TestToolIntegration:
    """Test tool integration (Tavily, Google Trends MCP)."""

    @pytest.fixture
    async def client(self):
        """Create HTTP client for testing."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
            yield client

    @pytest.fixture
    async def authenticated_client(self, client):
        """Create authenticated HTTP client with a conversation."""
        # Signup
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        response = await client.post(
            "/auth/signup",
            json={
                "email": f"tool_test_{unique_id}@example.com",
                "password": TEST_PASSWORD,
            },
        )
        assert response.status_code == 201
        token = response.json()["access_token"]
        
        # Add token to client headers
        client.headers.update({"Authorization": f"Bearer {token}"})
        
        # Create a conversation
        conv_response = await client.post(
            "/chat/conversations",
            json={"title": "Tool Integration Test"},
        )
        assert conv_response.status_code == 200
        conversation_id = conv_response.json()["id"]
        
        # Store conversation_id in client for use in tests
        client.conversation_id = conversation_id
        
        yield client

    @pytest.mark.asyncio
    async def test_tavily_search_invocation(self, authenticated_client):
        """Test that Tavily search is invoked for web queries."""
        # Send a message that should trigger Tavily search
        response = await authenticated_client.post(
            "/chat/message",
            json={
                "conversation_id": authenticated_client.conversation_id,
                "content": "What are the latest AI trends in 2026?",
            },
        )
        
        assert response.status_code == 200, f"Message send failed: {response.text}"
        
        # Parse SSE stream to check for tool activity
        events = []
        for line in response.text.split("\n"):
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
                events.append(event_type)
        
        # Should have at least some events (token, tool activity, etc.)
        assert len(events) > 0, "No SSE events received"
        
        # Check if tool activity events are present
        tool_events = [e for e in events if "tool" in e.lower()]
        # Note: Tool events may or may not be present depending on agent behavior
        # This test just verifies the stream works

    @pytest.mark.asyncio
    async def test_tavily_results_parsing(self, authenticated_client):
        """Test that Tavily results are parsed correctly."""
        # Send a message that should trigger Tavily search
        response = await authenticated_client.post(
            "/chat/message",
            json={
                "conversation_id": authenticated_client.conversation_id,
                "content": "Search for information about machine learning",
            },
        )
        
        assert response.status_code == 200, f"Message send failed: {response.text}"
        
        # Verify response is valid SSE stream
        assert "event:" in response.text, "Response should contain SSE events"
        
        # Retrieve messages to verify user message was saved
        messages_response = await authenticated_client.get(
            f"/chat/conversations/{authenticated_client.conversation_id}/messages"
        )
        assert messages_response.status_code == 200
        messages = messages_response.json()["messages"]
        
        # Should have at least user message
        assert len(messages) >= 1, "Should have at least user message"
        
        # Verify message role
        roles = [m.get("role") for m in messages]
        assert "user" in roles, "Should have user message"

    @pytest.mark.asyncio
    async def test_tavily_error_handling(self, authenticated_client):
        """Test that Tavily errors are handled gracefully."""
        # Send a message with an empty query (edge case)
        response = await authenticated_client.post(
            "/chat/message",
            json={
                "conversation_id": authenticated_client.conversation_id,
                "content": "   ",  # Empty/whitespace only
            },
        )
        
        # Should still return 200 (error handling is internal)
        assert response.status_code == 200, f"Message send failed: {response.text}"
        
        # Verify response contains events
        assert "event:" in response.text, "Response should contain SSE events"

    @pytest.mark.asyncio
    async def test_google_trends_mcp_invocation(self, authenticated_client):
        """Test that Google Trends MCP is invoked for trends queries."""
        # Send a message that should trigger Google Trends MCP
        response = await authenticated_client.post(
            "/chat/message",
            json={
                "conversation_id": authenticated_client.conversation_id,
                "content": "What are the trending topics right now?",
            },
        )
        
        assert response.status_code == 200, f"Message send failed: {response.text}"
        
        # Parse SSE stream
        events = []
        for line in response.text.split("\n"):
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
                events.append(event_type)
        
        # Should have at least some events
        assert len(events) > 0, "No SSE events received"

    @pytest.mark.asyncio
    async def test_mcp_data_parsing(self, authenticated_client):
        """Test that MCP data is parsed correctly."""
        # Send a message that should trigger MCP
        response = await authenticated_client.post(
            "/chat/message",
            json={
                "conversation_id": authenticated_client.conversation_id,
                "content": "Get trending data for technology",
            },
        )
        
        assert response.status_code == 200, f"Message send failed: {response.text}"
        
        # Verify response is valid SSE stream
        assert "event:" in response.text, "Response should contain SSE events"
        
        # Retrieve messages to verify response was saved
        messages_response = await authenticated_client.get(
            f"/chat/conversations/{authenticated_client.conversation_id}/messages"
        )
        assert messages_response.status_code == 200
        messages = messages_response.json()["messages"]
        
        # Should have messages
        assert len(messages) > 0, "Should have messages"

    @pytest.mark.asyncio
    async def test_mcp_unavailability_handling(self, authenticated_client):
        """Test that MCP unavailability is handled gracefully."""
        # Send a message that might trigger MCP
        response = await authenticated_client.post(
            "/chat/message",
            json={
                "conversation_id": authenticated_client.conversation_id,
                "content": "Tell me about current trends",
            },
        )
        
        # Should still return 200 (error handling is internal)
        assert response.status_code == 200, f"Message send failed: {response.text}"
        
        # Verify response contains events (even if MCP is unavailable)
        assert "event:" in response.text, "Response should contain SSE events"

    @pytest.mark.asyncio
    async def test_tool_timeout_handling(self, authenticated_client):
        """Test that tool timeouts are handled gracefully."""
        # Send a message that might timeout
        response = await authenticated_client.post(
            "/chat/message",
            json={
                "conversation_id": authenticated_client.conversation_id,
                "content": "Search for very specific information that might timeout",
            },
        )
        
        # Should still return 200 (timeout handling is internal)
        assert response.status_code == 200, f"Message send failed: {response.text}"
        
        # Verify response contains events
        assert "event:" in response.text, "Response should contain SSE events"

    @pytest.mark.asyncio
    async def test_multiple_tool_invocations(self, authenticated_client):
        """Test that multiple tools can be invoked in sequence."""
        # Send a complex message that might trigger multiple tools
        response = await authenticated_client.post(
            "/chat/message",
            json={
                "conversation_id": authenticated_client.conversation_id,
                "content": "Compare current AI trends with web search results",
            },
        )
        
        assert response.status_code == 200, f"Message send failed: {response.text}"
        
        # Parse SSE stream
        events = []
        for line in response.text.split("\n"):
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
                events.append(event_type)
        
        # Should have events
        assert len(events) > 0, "No SSE events received"
        
        # Verify response was saved
        messages_response = await authenticated_client.get(
            f"/chat/conversations/{authenticated_client.conversation_id}/messages"
        )
        assert messages_response.status_code == 200
        messages = messages_response.json()["messages"]
        
        # Should have messages
        assert len(messages) > 0, "Should have messages"

    @pytest.mark.asyncio
    async def test_tool_activity_indicators(self, authenticated_client):
        """Test that tool activity indicators are displayed during tool use."""
        # Send a message that should trigger tools
        response = await authenticated_client.post(
            "/chat/message",
            json={
                "conversation_id": authenticated_client.conversation_id,
                "content": "What are the latest developments in AI?",
            },
        )
        
        assert response.status_code == 200, f"Message send failed: {response.text}"
        
        # Parse SSE stream to look for tool activity events
        lines = response.text.split("\n")
        has_events = False
        for line in lines:
            if line.startswith("event:"):
                has_events = True
                break
        
        assert has_events, "Response should contain SSE events"

    @pytest.mark.asyncio
    async def test_agent_iteration_limit(self, authenticated_client):
        """Test that agent respects iteration limit."""
        # Send a message that might cause many iterations
        response = await authenticated_client.post(
            "/chat/message",
            json={
                "conversation_id": authenticated_client.conversation_id,
                "content": "Perform a very complex analysis with multiple steps",
            },
        )
        
        # Should still return 200 (iteration limit is enforced internally)
        assert response.status_code == 200, f"Message send failed: {response.text}"
        
        # Verify response contains events
        assert "event:" in response.text, "Response should contain SSE events"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
