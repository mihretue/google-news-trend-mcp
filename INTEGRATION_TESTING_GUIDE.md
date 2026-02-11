# Integration Testing Guide

This guide explains how to run the integration tests for the LangChain ReAct Chatbot system.

## Overview

Integration tests validate end-to-end flows across the entire system:
- **Authentication Flow**: Signup → Login → Chat Access
- **Chat Flow**: Create Conversation → Send Message → Receive Response → Save to DB
- **User Isolation**: Verify users can only see their own data
- **Error Handling**: Validate error responses and graceful degradation

## Prerequisites

1. **Backend running**: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. **Supabase project**: Configured with conversations and messages tables
3. **Environment variables**: Set in `backend/.env`
4. **Python dependencies**: `pip install -r backend/requirements.txt`

## Test Files

### 1. `test_integration_auth.py`
Tests end-to-end authentication flow:
- Signup creates user and returns token
- Login with valid credentials returns token
- Login with invalid credentials is rejected
- Token enables chat access
- Missing token blocks access
- Invalid token blocks access
- Public endpoints bypass authentication

**Run:**
```bash
cd backend
pytest test_integration_auth.py -v
```

### 2. `test_integration_chat.py`
Tests end-to-end chat flow:
- Create conversation
- List conversations
- Get conversation messages
- Send message and receive response
- Message saved to database
- Chat history restoration
- Unauthorized access to other users' conversations

**Run:**
```bash
cd backend
pytest test_integration_chat.py -v
```

### 3. `test_integration_isolation.py`
Tests user isolation and error handling:
- User cannot see other users' conversations
- RLS prevents unauthorized database access
- Invalid input returns 422
- Message length validation
- Error response format
- Health check endpoint
- Duplicate email signup rejected
- Weak password rejected
- Invalid email rejected

**Run:**
```bash
cd backend
pytest test_integration_isolation.py -v
```

## Running All Integration Tests

```bash
cd backend
pytest test_integration_*.py -v
```

## Running Specific Test

```bash
cd backend
pytest test_integration_auth.py::TestAuthenticationFlow::test_signup_creates_user_and_returns_token -v
```

## Expected Results

All tests should pass with output like:
```
test_integration_auth.py::TestAuthenticationFlow::test_signup_creates_user_and_returns_token PASSED
test_integration_auth.py::TestAuthenticationFlow::test_login_with_valid_credentials_returns_token PASSED
...
```

## Troubleshooting

### Connection Refused
- Ensure backend is running on `http://localhost:8000`
- Check firewall settings

### 401 Unauthorized
- Verify Supabase credentials in `.env`
- Check JWT secret is correct

### 422 Unprocessable Entity
- Verify request body matches schema
- Check required fields are present

### Timeout
- Increase timeout in test file (default 30-60 seconds)
- Check backend performance

## Test Coverage

The integration tests cover:
- ✅ Authentication (signup, login, token validation)
- ✅ Chat operations (create, list, send messages)
- ✅ User isolation (RLS, data privacy)
- ✅ Error handling (validation, authorization)
- ✅ Database persistence (messages saved correctly)
- ✅ Public endpoints (health check)

## Notes

- Tests use unique emails with timestamps to avoid conflicts
- Each test is independent and can run in any order
- Tests clean up after themselves (no manual cleanup needed)
- Tests use real Supabase database (not mocked)
- Tests validate both happy path and error cases

## Next Steps

After integration tests pass:
1. Run frontend integration tests (if available)
2. Test Docker Compose startup
3. Verify end-to-end flow in browser
4. Load testing (optional)
5. Security testing (optional)
