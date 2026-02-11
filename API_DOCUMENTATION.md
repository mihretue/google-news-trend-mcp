# LangChain ReAct Chatbot API Documentation

## Overview

This document describes all API endpoints for the LangChain ReAct Chatbot system. The API uses JWT token-based authentication and returns JSON responses.

## Base URL

```
http://localhost:8000
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

Tokens are obtained from the signup or login endpoints and are valid for 1 hour.

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid authentication token
- `403 Forbidden` - User lacks permission to access resource
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists (e.g., duplicate email)
- `422 Unprocessable Entity` - Invalid input data
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

## Authentication Endpoints

### POST /auth/signup

Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Parameters:**
- `email` (string, required): User email address
- `password` (string, required): User password (minimum 8 characters, must include uppercase, lowercase, numbers, and special characters)

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJFUzI1NiIsImtpZCI6IjViZjMzOTU5LWVjMGUtNDdjNC1iODFjLTFlZDc4YWMyOTJiOCIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid email or weak password
- `409 Conflict` - Email already registered
- `422 Unprocessable Entity` - Invalid input format

**Example:**
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

---

### POST /auth/login

Authenticate user with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Parameters:**
- `email` (string, required): User email address
- `password` (string, required): User password

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJFUzI1NiIsImtpZCI6IjViZjMzOTU5LWVjMGUtNDdjNC1iODFjLTFlZDc4YWMyOTJiOCIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid email or password
- `403 Forbidden` - Email not confirmed
- `429 Too Many Requests` - Too many login attempts

**Example:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

---

### POST /auth/logout

Logout user (frontend-side token removal).

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/auth/logout
```

---

## Chat Endpoints

### POST /chat/conversations

Create a new conversation.

**Authentication:** Required

**Request:**
```json
{
  "title": "AI Trends Discussion"
}
```

**Parameters:**
- `title` (string, required): Conversation title (1-255 characters)

**Response (200 OK):**
```json
{
  "id": "928afd6e-fa9e-41f9-8cca-1195764fa3b4",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "AI Trends Discussion",
  "created_at": "2026-02-11T08:52:48.932019Z",
  "updated_at": "2026-02-11T08:52:48.932019Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `422 Unprocessable Entity` - Invalid title

**Example:**
```bash
curl -X POST http://localhost:8000/chat/conversations \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI Trends Discussion"
  }'
```

---

### GET /chat/conversations

List all conversations for the current user.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "conversations": [
    {
      "id": "928afd6e-fa9e-41f9-8cca-1195764fa3b4",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "AI Trends Discussion",
      "created_at": "2026-02-11T08:52:48.932019Z",
      "updated_at": "2026-02-11T08:52:48.932019Z"
    }
  ],
  "count": 1
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token

**Example:**
```bash
curl -X GET http://localhost:8000/chat/conversations \
  -H "Authorization: Bearer <access_token>"
```

---

### GET /chat/conversations/{conversation_id}/messages

Get all messages for a conversation.

**Authentication:** Required

**Parameters:**
- `conversation_id` (string, path, required): Conversation ID

**Response (200 OK):**
```json
{
  "conversation_id": "928afd6e-fa9e-41f9-8cca-1195764fa3b4",
  "messages": [
    {
      "id": "c44342e3-c664-4054-8a7c-d3560f57b372",
      "conversation_id": "928afd6e-fa9e-41f9-8cca-1195764fa3b4",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "user",
      "content": "What are the latest AI trends?",
      "tool_calls": null,
      "created_at": "2026-02-11T08:52:48.932019Z"
    },
    {
      "id": "d55453f4-d775-5165-9b8d-e4671f68c483",
      "conversation_id": "928afd6e-fa9e-41f9-8cca-1195764fa3b4",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "assistant",
      "content": "Based on recent trends, the top AI developments include...",
      "tool_calls": null,
      "created_at": "2026-02-11T08:52:50.123456Z"
    }
  ],
  "count": 2
}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - User does not own this conversation
- `404 Not Found` - Conversation not found

**Example:**
```bash
curl -X GET http://localhost:8000/chat/conversations/928afd6e-fa9e-41f9-8cca-1195764fa3b4/messages \
  -H "Authorization: Bearer <access_token>"
```

---

### POST /chat/message

Send a message and stream the agent response via Server-Sent Events (SSE).

**Authentication:** Required

**Request:**
```json
{
  "conversation_id": "928afd6e-fa9e-41f9-8cca-1195764fa3b4",
  "content": "What are the latest AI trends?"
}
```

**Parameters:**
- `conversation_id` (string, required): Conversation ID
- `content` (string, required): Message content (1-4096 characters)

**Response (200 OK - Server-Sent Events Stream):**

The response is a stream of Server-Sent Events (SSE). Each event has the format:

```
event: <event_type>
data: <json_data>

```

**Event Types:**

1. **token** - Agent response token
```
event: token
data: {"token": "The"}

event: token
data: {"token": " latest"}

event: token
data: {"token": " AI"}
```

2. **tool_activity** - Tool invocation activity
```
event: tool_activity
data: {"tool": "tavily_search", "status": "started"}

event: tool_activity
data: {"tool": "tavily_search", "status": "completed"}
```

3. **done** - Response complete
```
event: done
data: {"message_id": "d55453f4-d775-5165-9b8d-e4671f68c483"}
```

4. **error** - Error occurred
```
event: error
data: {"error": "Tool invocation failed"}
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - User does not own this conversation
- `404 Not Found` - Conversation not found
- `422 Unprocessable Entity` - Invalid message content

**Example:**
```bash
curl -X POST http://localhost:8000/chat/message \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "928afd6e-fa9e-41f9-8cca-1195764fa3b4",
    "content": "What are the latest AI trends?"
  }'
```

**JavaScript Example:**
```javascript
const eventSource = new EventSource(
  'http://localhost:8000/chat/message',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      content: 'What are the latest AI trends?'
    })
  }
);

eventSource.addEventListener('token', (event) => {
  const data = JSON.parse(event.data);
  console.log('Token:', data.token);
});

eventSource.addEventListener('tool_activity', (event) => {
  const data = JSON.parse(event.data);
  console.log('Tool:', data.tool, 'Status:', data.status);
});

eventSource.addEventListener('done', (event) => {
  const data = JSON.parse(event.data);
  console.log('Message complete:', data.message_id);
  eventSource.close();
});

eventSource.addEventListener('error', (event) => {
  const data = JSON.parse(event.data);
  console.error('Error:', data.error);
  eventSource.close();
});
```

---

## Health Check Endpoint

### GET /health

Check system health and service connectivity.

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "unhealthy",
  "details": "Supabase connection failed"
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/health
```

---

## Rate Limiting

The API implements rate limiting to prevent abuse:
- **Signup/Login**: 5 attempts per 15 minutes per IP
- **Chat messages**: 100 messages per hour per user
- **General API**: 1000 requests per hour per user

When rate limited, the API returns `429 Too Many Requests`.

---

## CORS

The API supports Cross-Origin Resource Sharing (CORS) for requests from the frontend:
- **Allowed Origins**: `http://localhost:3000` (development)
- **Allowed Methods**: GET, POST, OPTIONS
- **Allowed Headers**: Content-Type, Authorization

---

## Pagination

List endpoints support pagination via query parameters:
- `limit` (integer, optional): Number of items to return (default: 50, max: 100)
- `offset` (integer, optional): Number of items to skip (default: 0)

Example:
```bash
curl -X GET "http://localhost:8000/chat/conversations?limit=10&offset=0" \
  -H "Authorization: Bearer <access_token>"
```

---

## Versioning

The API uses URL-based versioning. Current version is v1 (implicit in all endpoints).

Future versions will use paths like `/api/v2/...`

---

## Webhooks (Future)

Webhook support is planned for future releases to notify external systems of:
- New messages
- Conversation updates
- Tool invocations
- Errors

---

## Support

For issues or questions about the API:
1. Check the [Integration Testing Guide](INTEGRATION_TESTING_GUIDE.md)
2. Review the [README](README.md) for setup instructions
3. Check logs for detailed error information

---

## Changelog

### Version 1.0 (Current)
- Initial API release
- Authentication endpoints (signup, login, logout)
- Chat endpoints (conversations, messages, streaming)
- Health check endpoint
- Tool integration (Tavily, Google Trends MCP)
- User isolation via RLS
- Error handling and validation
