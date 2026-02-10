# Design Document: LangChain ReAct Chatbot System

## Overview

A full-stack LangChain ReAct chatbot system that orchestrates intelligent agent reasoning with tool selection, streaming responses, and persistent chat memory. The system uses FastAPI for the backend, React TypeScript for the frontend, Supabase for authentication and data persistence, and Docker Compose for orchestration. The ReAct agent intelligently selects between Tavily web search and Google Trends MCP based on query intent, with streaming responses delivered via Server-Sent Events (SSE).

## Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Frontend   │  │   Backend    │  │  Google      │           │
│  │   (React)    │  │  (FastAPI)   │  │  Trends MCP  │           │
│  │   :3000      │  │   :8000      │  │  :5000       │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│         │                  │                                      │
│         └──────────────────┼──────────────────┐                  │
│                            │                  │                  │
│                    ┌───────▼────────┐  ┌──────▼──────┐           │
│                    │   Supabase     │  │   Tavily    │           │
│                    │   (Auth + DB)  │  │   (External)│           │
│                    └────────────────┘  └─────────────┘           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

**1. Why SSE vs WebSocket for Streaming**

SSE (Server-Sent Events) is chosen over WebSocket for the following reasons:
- Simpler protocol: HTTP-based, no bidirectional complexity
- Built-in reconnection: Automatic client-side reconnection with exponential backoff
- Easier debugging: Standard HTTP tools work without special WebSocket inspection
- Sufficient for use case: Unidirectional streaming (server → client) is all we need
- Better error handling: HTTP status codes and standard error semantics
- Reduced complexity: No need for connection state management on both sides

**2. ReAct Agent Tool Selection Logic**

The agent uses a multi-step reasoning process:
- **Intent Classification**: LLM analyzes query to determine if it's about trends, web search, or general knowledge
- **Tool Routing**: Based on intent, agent selects appropriate tool(s)
- **Fallback Strategy**: If primary tool fails, agent can attempt alternative or respond with available knowledge
- **Iteration Limit**: Maximum 10 iterations to prevent infinite loops

Tool selection heuristics:
- Queries containing keywords like "trending", "popular", "top", "viral" → Google Trends MCP
- Queries requiring current information, news, or recent events → Tavily Search
- General knowledge questions → Direct LLM response (no tools)
- Ambiguous queries → Agent decides based on reasoning

**3. MCP Adapter Integration with LangChain**

The Google Trends MCP is integrated via:
- **MCP Client Wrapper**: Custom Python wrapper that communicates with MCP server via stdio/HTTP
- **Tool Definition**: MCP tool is registered as a LangChain Tool with input schema and description
- **Error Handling**: Wrapper catches MCP errors and returns structured error responses
- **Timeout Management**: Requests to MCP have configurable timeout (default 10s)
- **Docker Network**: MCP server runs in separate container, accessed via service name (not localhost)

**4. Supabase RLS for Data Isolation**

Row-Level Security policies enforce user isolation at the database level:
- **Auth Policy**: All queries automatically filtered by `auth.uid()` matching `user_id`
- **Conversation Policy**: Users can only access conversations where `user_id = auth.uid()`
- **Message Policy**: Users can only access messages in their own conversations
- **Enforcement**: RLS is enabled on all tables; no application-level filtering needed
- **Fallback**: Application-level checks provide defense-in-depth

**5. Chat Memory Loading into Agent Context**

Memory management follows this pattern:
- **Retrieval**: On each message, fetch last N messages (default 10) from database
- **Formatting**: Messages formatted as LangChain Message objects with role and content
- **Context Window**: Recent messages loaded into agent's system prompt
- **Summarization**: For long conversations, older messages can be summarized (future enhancement)
- **Isolation**: Only messages from current conversation and current user are loaded

**6. Middleware Access Control**

Middleware enforces authentication and authorization:
- **Token Extraction**: Bearer token extracted from Authorization header
- **Token Validation**: Token verified against Supabase JWT secret
- **User Extraction**: User ID extracted from token claims
- **Request Annotation**: User ID attached to request context for downstream use
- **Public Routes**: `/auth/signup`, `/auth/login`, `/health` bypass authentication
- **Protected Routes**: `/chat/*`, `/conversations/*` require valid token

**7. Docker Networking Strategy**

Services communicate via Docker Compose network:
- **Service Names**: Backend uses `http://mcp:5000` instead of `localhost:5000`
- **Environment Variables**: Service URLs passed via .env file
- **Network Isolation**: Only exposed ports are frontend (3000) and backend (8000)
- **Internal Communication**: MCP, Supabase accessed only via internal network
- **Health Checks**: Each service has health check endpoint for readiness verification

**8. Failure Handling and Graceful Degradation**

System handles failures gracefully:
- **Tool Failures**: Agent continues with alternative tools or responds with available knowledge
- **MCP Unavailability**: System returns friendly error; agent can still use Tavily or respond directly
- **Database Unavailability**: User receives error; backend doesn't crash
- **Timeout Handling**: Long-running operations cancelled; user informed
- **Partial Failures**: If one tool fails, agent attempts others before giving up
- **Error Logging**: All errors logged internally with user_id and request_id for debugging

## Components and Interfaces

### Frontend Components

**Authentication Module** (`frontend/src/pages/Auth.tsx`)
- Login form with email/password inputs
- Signup form with email/password/confirm password
- Error display and loading states
- Token storage in localStorage
- Redirect to chat on successful auth

**Chat Interface** (`frontend/src/pages/Chat.tsx`)
- Message list with user and agent messages
- Input field for user messages
- Tool activity indicators (e.g., "Searching web…")
- Auto-scroll to latest message
- Loading state during streaming

**Message Component** (`frontend/src/components/Message.tsx`)
- Render user or agent message
- Streaming token display for agent messages
- Tool activity indicator display
- Timestamp display

**API Client** (`frontend/src/api/chatClient.ts`)
- SSE connection management
- Token streaming handler
- Tool activity event handler
- Error handling and reconnection logic

### Backend Components

**FastAPI Application** (`backend/app/main.py`)
- CORS middleware configuration
- Authentication middleware
- Route registration
- Startup/shutdown events

**Authentication Router** (`backend/app/routers/auth.py`)
- POST `/auth/signup` - Create new user
- POST `/auth/login` - Authenticate user
- POST `/auth/logout` - Clear session

**Chat Router** (`backend/app/routers/chat.py`)
- POST `/chat/message` - Send message and stream response
- GET `/chat/conversations` - List user's conversations
- GET `/chat/conversations/{id}/messages` - Get conversation messages

**Health Router** (`backend/app/routers/health.py`)
- GET `/health` - Service health status
- Checks Supabase connectivity
- Checks MCP connectivity

**ReAct Agent Service** (`backend/app/services/agent/react_agent.py`)
- Agent initialization with tools
- Message processing and reasoning
- Tool invocation and result handling
- Iteration limit enforcement
- Streaming response generation

**Tool Services**
- `backend/app/services/tools/tavily.py` - Tavily search wrapper
- `backend/app/services/tools/google_trends_mcp.py` - MCP client wrapper

**Database Service** (`backend/app/services/db/supabase_client.py`)
- User authentication
- Message persistence
- Conversation management
- Chat history retrieval

**Middleware** (`backend/app/middleware/auth.py`)
- Token extraction and validation
- User context injection
- Public route bypass

### Data Models

**User** (Supabase Auth)
- id: UUID
- email: string
- created_at: timestamp

**Conversation**
- id: UUID
- user_id: UUID (FK to User)
- title: string
- created_at: timestamp
- updated_at: timestamp

**Message**
- id: UUID
- conversation_id: UUID (FK to Conversation)
- user_id: UUID (FK to User)
- role: enum (user, assistant)
- content: text
- tool_calls: JSON (optional)
- created_at: timestamp

**Tool Call Metadata**
- tool_name: string
- input: JSON
- output: JSON
- execution_time_ms: integer
- error: string (optional)

## Data Models

### Supabase Schema

```sql
-- Users table (managed by Supabase Auth)
CREATE TABLE auth.users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Conversations table
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Messages table
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  tool_calls JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Row-Level Security Policies
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only access their own conversations"
  ON conversations FOR ALL
  USING (auth.uid() = user_id);

CREATE POLICY "Users can only access their own messages"
  ON messages FOR ALL
  USING (auth.uid() = user_id);
```

### API Request/Response Schemas

**Chat Message Request**
```json
{
  "conversation_id": "uuid",
  "content": "string (max 4096 chars)",
  "user_id": "uuid (from token)"
}
```

**SSE Response Stream**
```
event: token
data: {"token": "Hello"}

event: token
data: {"token": " world"}

event: tool_activity
data: {"tool": "tavily_search", "status": "started"}

event: tool_activity
data: {"tool": "tavily_search", "status": "completed"}

event: done
data: {"message_id": "uuid"}
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Authentication Properties

**Property 1: Signup creates user and returns token**
*For any* valid email and password, signing up should create a user in Supabase and return a valid JWT token that can be used for subsequent requests.
**Validates: Requirements 1.1**

**Property 2: Login with valid credentials returns token**
*For any* user that exists in the system, logging in with their correct email and password should return a valid JWT token.
**Validates: Requirements 1.2**

**Property 3: Login with invalid credentials is rejected**
*For any* email and password combination that doesn't match an existing user, login should be rejected with an error message.
**Validates: Requirements 1.3**

**Property 4: Token enables chat access**
*For any* valid JWT token, requests to protected endpoints with that token should be allowed to proceed.
**Validates: Requirements 1.4, 9.1**

**Property 5: Missing token blocks access**
*For any* protected endpoint, requests without an authentication token should be rejected with 401 Unauthorized.
**Validates: Requirements 9.2**

**Property 6: Invalid token blocks access**
*For any* protected endpoint, requests with an invalid or malformed token should be rejected with 401 Unauthorized.
**Validates: Requirements 9.3, 9.4**

### Chat and Streaming Properties

**Property 7: User messages appear immediately**
*For any* user message sent via the chat API, the message should appear in the UI immediately before the agent responds.
**Validates: Requirements 2.1**

**Property 8: Agent responses stream incrementally**
*For any* agent response, tokens should arrive incrementally via SSE rather than all at once.
**Validates: Requirements 2.2**

**Property 9: Tool activity indicators display during tool use**
*For any* tool invocation, a tool activity indicator should be displayed in the UI while the tool is executing.
**Validates: Requirements 2.3**

**Property 10: Tool indicators clear after completion**
*For any* completed tool invocation, the tool activity indicator should be cleared from the UI.
**Validates: Requirements 2.4**

**Property 11: Chat history persists and restores**
*For any* conversation, after sending messages and refreshing the page, all messages should be restored from the database.
**Validates: Requirements 2.5, 6.1, 6.2, 6.3**

### Tool Selection Properties

**Property 12: Trends queries invoke Google Trends MCP**
*For any* query about trends, popularity, or viral content, the agent should invoke the Google_Trends_MCP tool.
**Validates: Requirements 3.1**

**Property 13: Web queries invoke Tavily Search**
*For any* query requiring current web information or recent events, the agent should invoke the Tavily_Search tool.
**Validates: Requirements 3.2**

**Property 14: Agent waits for tool responses**
*For any* tool invocation, the agent should wait for the tool to complete before continuing reasoning.
**Validates: Requirements 3.4**

**Property 15: Tool errors are handled gracefully**
*For any* tool that returns an error, the agent should handle the error and provide a fallback response.
**Validates: Requirements 3.5, 15.1**

**Property 16: Iteration limit stops reasoning**
*For any* agent reasoning process that reaches the maximum iteration limit, the agent should stop and return the best available response.
**Validates: Requirements 3.6, 18.1**

### Tool Integration Properties

**Property 17: Tavily search calls API correctly**
*For any* search query, the Tavily_Search tool should call the Tavily API with the correct query parameter.
**Validates: Requirements 4.1**

**Property 18: Tavily results are parsed correctly**
*For any* Tavily API response, the results should be parsed and provided to the agent in the correct format.
**Validates: Requirements 4.2**

**Property 19: Tavily failures are handled**
*For any* Tavily API failure, the system should log the error and return a user-friendly error message.
**Validates: Requirements 4.3**

**Property 20: Empty Tavily results are handled**
*For any* search query that returns no results, the agent should be informed of the empty result set.
**Validates: Requirements 4.4**

**Property 21: MCP communicates via Docker network**
*For any* Google_Trends_MCP invocation, the system should communicate with the MCP server via the Docker network using service names.
**Validates: Requirements 5.1, 10.2, 10.3**

**Property 22: MCP data is parsed correctly**
*For any* MCP response, the trend data should be parsed and provided to the agent in the correct format.
**Validates: Requirements 5.2**

**Property 23: MCP unavailability is handled gracefully**
*For any* MCP service that is unavailable, the system should return a friendly error message and continue operation.
**Validates: Requirements 5.3, 15.2**

**Property 24: MCP timeouts are handled**
*For any* MCP request that exceeds the timeout threshold, the system should cancel the request and inform the agent.
**Validates: Requirements 5.4, 18.2**

### Data Persistence Properties

**Property 25: Messages are saved with correct metadata**
*For any* user message, the system should save it to the database with user_id, conversation_id, role, content, and timestamp.
**Validates: Requirements 6.1**

**Property 26: Agent responses are saved with correct metadata**
*For any* agent response, the system should save it to the database with the same metadata as user messages.
**Validates: Requirements 6.2**

**Property 27: Conversation history is retrieved correctly**
*For any* conversation, loading the chat interface should retrieve all messages for that conversation from the database.
**Validates: Requirements 6.3**

**Property 28: New conversations are created correctly**
*For any* new conversation, the system should create a new conversation record and associate subsequent messages with it.
**Validates: Requirements 6.4**

**Property 29: Agent context includes conversation history**
*For any* message processed by the agent, the system should load recent conversation history into the agent context.
**Validates: Requirements 6.5**

### User Isolation Properties

**Property 30: Users only see their own data**
*For any* user querying the database, the system should only return data associated with that user.
**Validates: Requirements 7.1**

**Property 31: User B cannot see User A's conversations**
*For any* two different users, User B should not be able to access User A's conversations or messages.
**Validates: Requirements 7.2**

**Property 32: Missing token returns 401**
*For any* request with a missing authentication token, the system should reject it with 401 Unauthorized.
**Validates: Requirements 7.3**

**Property 33: Cross-user access returns 403**
*For any* request with a valid token attempting to access another user's data, the system should reject it with 403 Forbidden.
**Validates: Requirements 7.4**

**Property 34: RLS prevents unauthorized database access**
*For any* direct database query, Supabase RLS policies should prevent access to other users' data.
**Validates: Requirements 7.5**

### API and Validation Properties

**Property 35: Missing fields return 422**
*For any* API request missing required fields, the system should return a 422 Unprocessable Entity error.
**Validates: Requirements 8.1, 16.1**

**Property 36: Invalid types return 422**
*For any* API request with invalid data types, the system should return a 422 error with field-specific messages.
**Validates: Requirements 8.2, 16.2**

**Property 37: SSE connection streams tokens**
*For any* valid message request, the backend should establish an SSE connection and stream response tokens.
**Validates: Requirements 8.2**

**Property 38: Tool activity events are emitted**
*For any* tool invocation, the backend should emit a tool activity event via SSE.
**Validates: Requirements 8.3**

**Property 39: SSE connection closes after response**
*For any* completed response, the backend should close the SSE connection.
**Validates: Requirements 8.4**

**Property 40: Client disconnect triggers cleanup**
*For any* client that disconnects during streaming, the backend should stop processing and clean up resources.
**Validates: Requirements 8.5**

**Property 41: CORS blocks unknown origins**
*For any* request from an unknown origin, the system should reject it based on CORS policy.
**Validates: Requirements 8.6**

### Middleware Properties

**Property 42: Valid token allows request**
*For any* request to a protected endpoint with a valid token, the middleware should allow the request to proceed.
**Validates: Requirements 9.1**

**Property 43: Public endpoints bypass authentication**
*For any* request to a public endpoint, the middleware should allow the request without authentication.
**Validates: Requirements 9.5**

### Docker and Infrastructure Properties

**Property 44: Docker Compose starts all services**
*For any* docker compose up --build command, the system should start all services (frontend, backend, MCP, Supabase).
**Validates: Requirements 10.1**

**Property 45: Services communicate via Docker network**
*For any* service-to-service communication, the system should use Docker service names instead of localhost.
**Validates: Requirements 10.2, 10.3**

**Property 46: Health checks verify readiness**
*For any* service startup, the system should perform health checks to verify readiness.
**Validates: Requirements 10.4, 11.1, 11.2, 11.3**

**Property 47: Unhealthy services return 503**
*For any* service that is not ready, the health check should return 503 Service Unavailable.
**Validates: Requirements 11.4**

**Property 48: Docker Compose waits for health checks**
*For any* Docker Compose startup, the system should wait for health checks to pass before considering services ready.
**Validates: Requirements 10.5, 11.5**

### Security Properties

**Property 49: API keys not logged**
*For any* backend request processing, the system should not log API keys or authentication tokens.
**Validates: Requirements 12.1**

**Property 50: Stack traces not exposed to client**
*For any* error that occurs, the system should not expose internal stack traces to the client.
**Validates: Requirements 12.2**

**Property 51: HTTPS used for external services**
*For any* backend communication with external services, the system should use secure HTTPS connections.
**Validates: Requirements 12.4**

**Property 52: Supabase credentials not in client code**
*For any* client-side code, Supabase credentials should not be exposed.
**Validates: Requirements 12.5**

### Containerization Properties

**Property 53: Frontend container serves on port 3000**
*For any* frontend container startup, the system should serve the React application on port 3000.
**Validates: Requirements 13.2**

**Property 54: Frontend uses environment variables for backend URL**
*For any* frontend container, the backend API URL should be configured via environment variables.
**Validates: Requirements 13.3, 13.4**

**Property 55: Backend container starts FastAPI on port 8000**
*For any* backend container startup, the system should start the FastAPI server on port 8000.
**Validates: Requirements 14.2**

**Property 56: Backend uses environment variables for service URLs**
*For any* backend container, service URLs should be configured via environment variables.
**Validates: Requirements 14.3, 14.4**

### Error Handling Properties

**Property 57: Database unavailability doesn't crash backend**
*For any* database unavailability, the system should display an error and not crash the backend.
**Validates: Requirements 15.3**

**Property 58: Request timeout cancels operation**
*For any* request that exceeds the timeout threshold, the system should cancel the operation and inform the user.
**Validates: Requirements 15.4, 18.3**

**Property 59: Unexpected errors return generic message**
*For any* unexpected error, the system should log the error internally and return a generic error message to the user.
**Validates: Requirements 15.5**

### Input Validation Properties

**Property 60: Message length is validated**
*For any* message that exceeds maximum length, the system should reject the message and inform the user.
**Validates: Requirements 16.3**

**Property 61: User input is sanitized**
*For any* user input, the system should sanitize it to prevent injection attacks.
**Validates: Requirements 16.4**

### Logging and Traceability Properties

**Property 62: Tool invocations are logged**
*For any* tool invocation, the system should log the tool name, input, and timestamp.
**Validates: Requirements 17.1**

**Property 63: Tool completions are logged**
*For any* tool completion, the system should log the tool output and execution time.
**Validates: Requirements 17.2**

**Property 64: Tool errors are logged internally**
*For any* tool error, the system should log the error and stack trace internally.
**Validates: Requirements 17.3**

**Property 65: Logs include user_id and request_id**
*For any* request processed, the system should associate logs with the user_id and request_id for traceability.
**Validates: Requirements 17.4**

## Error Handling

### Authentication Errors
- Invalid credentials: Return 401 with message "Invalid email or password"
- Token expired: Return 401 with message "Session expired, please log in again"
- Missing token: Return 401 with message "Authorization required"
- Invalid token format: Return 401 with message "Invalid authorization token"

### Tool Errors
- Tavily API failure: Log error, return "Unable to search the web at this time"
- MCP timeout: Log error, return "Trends service is taking too long, please try again"
- MCP unavailable: Log error, return "Trends service is currently unavailable"
- Tool parsing error: Log error, return "Error processing tool response"

### Database Errors
- Connection failure: Return 503 with message "Database service unavailable"
- Query timeout: Return 504 with message "Request timed out"
- RLS violation: Return 403 with message "Access denied"

### Validation Errors
- Missing fields: Return 422 with field-specific error messages
- Invalid types: Return 422 with type information
- Message too long: Return 422 with message "Message exceeds maximum length"

### Streaming Errors
- Client disconnect: Log and clean up resources
- SSE write failure: Log and close connection
- Agent error during streaming: Send error event and close connection

## Testing Strategy

### Unit Testing Approach

Unit tests validate specific examples, edge cases, and error conditions:

**Authentication Tests**
- Test signup with valid/invalid emails
- Test login with correct/incorrect passwords
- Test token validation and expiration
- Test logout functionality

**Tool Tests**
- Test Tavily search with various queries
- Test MCP communication and error handling
- Test tool result parsing
- Test timeout handling

**Database Tests**
- Test message persistence
- Test conversation creation
- Test RLS policy enforcement
- Test data retrieval

**API Tests**
- Test request validation
- Test CORS enforcement
- Test middleware authentication
- Test error responses

**Streaming Tests**
- Test SSE connection establishment
- Test token streaming
- Test tool activity events
- Test connection closure

### Property-Based Testing Approach

Property-based tests validate universal properties across all inputs using a PBT library (Hypothesis for Python, fast-check for TypeScript):

**Authentication Properties**
- Property 1: Signup creates user and returns token
- Property 2: Login with valid credentials returns token
- Property 3: Login with invalid credentials is rejected
- Property 4: Token enables chat access
- Property 5: Missing token blocks access
- Property 6: Invalid token blocks access

**Chat Properties**
- Property 7: User messages appear immediately
- Property 8: Agent responses stream incrementally
- Property 9: Tool activity indicators display
- Property 10: Tool indicators clear after completion
- Property 11: Chat history persists and restores

**Tool Properties**
- Property 12: Trends queries invoke Google Trends MCP
- Property 13: Web queries invoke Tavily Search
- Property 14: Agent waits for tool responses
- Property 15: Tool errors are handled gracefully
- Property 16: Iteration limit stops reasoning

**Data Isolation Properties**
- Property 30: Users only see their own data
- Property 31: User B cannot see User A's conversations
- Property 32: Missing token returns 401
- Property 33: Cross-user access returns 403
- Property 34: RLS prevents unauthorized database access

**Validation Properties**
- Property 35: Missing fields return 422
- Property 36: Invalid types return 422
- Property 60: Message length is validated
- Property 61: User input is sanitized

**Configuration Properties**
- Property 45: Services communicate via Docker network
- Property 54: Frontend uses environment variables
- Property 56: Backend uses environment variables

### Test Configuration

**Property-Based Test Requirements**
- Minimum 100 iterations per property test
- Each test tagged with feature name and property number
- Tag format: `Feature: langchain-react-chatbot, Property {N}: {property_text}`
- Tests use appropriate generators for input data
- Tests verify properties hold across all generated inputs

**Test Organization**
- Unit tests in `tests/unit/` directory
- Property tests in `tests/properties/` directory
- Integration tests in `tests/integration/` directory
- Fixtures and utilities in `tests/conftest.py`

**Test Execution**
- Unit tests: `pytest tests/unit/`
- Property tests: `pytest tests/properties/ -v`
- All tests: `pytest tests/`
- Coverage target: >80% for critical paths

