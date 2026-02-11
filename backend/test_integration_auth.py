"""
Integration tests for end-to-end authentication flow.
Tests: signup → login → chat access → logout
"""
import pytest
import httpx
import asyncio
from typing import Dict, Any

# Backend API base URL
BASE_URL = "http://localhost:8000"

# Test user credentials
TEST_EMAIL = "integration_test@example.com"
TEST_PASSWORD = "TestPassword123!"


class TestAuthenticationFlow:
    """Test end-to-end authentication flow."""

    @pytest.fixture
    async def client(self):
        """Create HTTP client for testing."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client

    @pytest.mark.asyncio
    async def test_signup_creates_user_and_returns_token(self, client):
        """Test that signup creates a user and returns a valid token."""
        # Signup with unique email
        unique_email = f"signup_test_{asyncio.get_event_loop().time()}@example.com"
        response = await client.post(
            "/auth/signup",
            json={
                "email": unique_email,
                "password": TEST_PASSWORD,
            },
        )
        
        assert response.status_code == 201, f"Signup failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data, "No access_token in response"
        assert "token_type" in data, "No token_type in response"
        assert "user_id" in data, "No user_id in response"
        assert "email" in data, "No email in response"
        
        # Verify token is not empty
        assert len(data["access_token"]) > 0, "Access token is empty"
        assert data["token_type"] == "bearer", "Invalid token type"
        assert data["email"] == unique_email, "Email mismatch"

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials_returns_token(self, client):
        """Test that login with valid credentials returns a token."""
        # First signup
        signup_response = await client.post(
            "/auth/signup",
            json={
                "email": f"login_test_{asyncio.get_event_loop().time()}@example.com",
                "password": TEST_PASSWORD,
            },
        )
        assert signup_response.status_code == 201
        signup_data = signup_response.json()
        test_email = signup_data["email"]
        
        # Then login
        login_response = await client.post(
            "/auth/login",
            json={
                "email": test_email,
                "password": TEST_PASSWORD,
            },
        )
        
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        data = login_response.json()
        
        # Verify response structure
        assert "access_token" in data, "No access_token in response"
        assert "token_type" in data, "No token_type in response"
        assert "user_id" in data, "No user_id in response"
        assert len(data["access_token"]) > 0, "Access token is empty"

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials_is_rejected(self, client):
        """Test that login with invalid credentials is rejected."""
        response = await client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPassword123!",
            },
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "No error detail in response"

    @pytest.mark.asyncio
    async def test_token_enables_chat_access(self, client):
        """Test that a valid token enables access to protected chat endpoints."""
        # Signup
        signup_response = await client.post(
            "/auth/signup",
            json={
                "email": f"chat_test_{asyncio.get_event_loop().time()}@example.com",
                "password": TEST_PASSWORD,
            },
        )
        assert signup_response.status_code == 201
        token = signup_response.json()["access_token"]
        
        # Try to access protected endpoint with token
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(
            "/chat/conversations",
            headers=headers,
        )
        
        assert response.status_code == 200, f"Chat access failed: {response.text}"
        data = response.json()
        assert "conversations" in data, "No conversations in response"

    @pytest.mark.asyncio
    async def test_missing_token_blocks_access(self, client):
        """Test that missing token blocks access to protected endpoints."""
        response = await client.get("/chat/conversations")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_invalid_token_blocks_access(self, client):
        """Test that invalid token blocks access to protected endpoints."""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = await client.get(
            "/chat/conversations",
            headers=headers,
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_public_endpoints_bypass_authentication(self, client):
        """Test that public endpoints don't require authentication."""
        # Health check should work without token
        response = await client.get("/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        
        # Signup should work without token
        response = await client.post(
            "/auth/signup",
            json={
                "email": f"public_test_{asyncio.get_event_loop().time()}@example.com",
                "password": TEST_PASSWORD,
            },
        )
        assert response.status_code == 201, f"Signup failed: {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
