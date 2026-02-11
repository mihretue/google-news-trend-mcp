# Implementation Plan: LangChain ReAct Chatbot System

## Overview

This implementation plan breaks down the LangChain ReAct chatbot system into discrete, incremental coding tasks. Each task builds on previous work, with property-based tests validating correctness properties throughout. The plan follows a layered approach: infrastructure setup, backend core, frontend core, tool integration, and finally integration and testing.

## Tasks

- [ ] 1. Project Setup and Infrastructure
  - [x] 1.1 Create project directory structure and Docker Compose configuration
    - Create root directory with frontend/, backend/, docker-compose.yml
    - Create .env.example with all required environment variables
    - Create README.md with setup instructions
    - _Requirements: 10.1, 13.1, 14.1_
  
  - [x] 1.2 Set up backend project structure and dependencies
    - Create backend/app/ directory structure (main.py, core/, middleware/, routers/, schemas/, services/, utils/)
    - Create backend/requirements.txt with FastAPI, LangChain, Supabase, Tavily dependencies
    - Create backend/Dockerfile for production image
    - Create backend/.env.example with Supabase and API keys
    - _Requirements: 14.1, 14.2_
  
  - [x] 1.3 Set up frontend project structure and dependencies
    - Create frontend/src/ directory structure (api/, components/, pages/, state/, types/, utils/)
    - Create frontend/package.json with React, TypeScript, Axios dependencies
    - Create frontend/Dockerfile for production image
    - Create frontend/.env.example with backend API URL
    - _Requirements: 13.1, 13.2_
  
  - [x] 1.4 Configure Supabase project and create database schema
    - Create Supabase project and obtain API keys
    - Create conversations and messages tables with RLS policies
    - Create indexes on user_id and conversation_id for query performance
    - Test RLS policies with multiple users
    - _Requirements: 6.1, 6.2, 7.1, 7.2, 7.5_

- [ ] 2. Backend Authentication and Middleware
  - [x] 2.1 Implement FastAPI application with CORS and middleware setup
    - Create backend/app/main.py with FastAPI app initialization
    - Configure CORS middleware to allow frontend origin
    - Set up request/response logging middleware
    - Create startup/shutdown event handlers
    - _Requirements: 8.6, 9.1, 9.2, 9.3_
  
  - [x] 2.2 Implement authentication middleware
    - Create backend/app/middleware/auth.py with token extraction and validation
    - Implement JWT token validation against Supabase secret
    - Extract user_id from token claims and attach to request context
    - Define public routes that bypass authentication
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ]* 2.3 Write property tests for authentication middleware
    - **Property 5: Missing token blocks access**
    - **Property 6: Invalid token blocks access**
    - **Property 42: Valid token allows request**
    - **Property 43: Public endpoints bypass authentication**
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [x] 2.4 Implement authentication router
    - Create backend/app/routers/auth.py with signup, login, logout endpoints
    - Implement signup: validate email/password, create Supabase user, return token
    - Implement login: validate credentials, return token
    - Implement logout: clear session (frontend-side token removal)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_
  
  - [ ]* 2.5 Write property tests for authentication endpoints
    - **Property 1: Signup creates user and returns token**
    - **Property 2: Login with valid credentials returns token**
    - **Property 3: Login with invalid credentials is rejected**
    - **Property 4: Token enables chat access**
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 3. Backend Health Checks and Validation
  - [x] 3.1 Implement health check router
    - Create backend/app/routers/health.py with /health endpoint
    - Check Supabase connectivity
    - Check MCP service connectivity
    - Return 200 OK if all healthy, 503 if any service unavailable
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  
  - [ ]* 3.2 Write property tests for health checks
    - **Property 46: Health checks verify readiness**
    - **Property 47: Unhealthy services return 503**
    - **Property 48: Docker Compose waits for health checks**
    - _Requirements: 10.4, 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [x] 3.3 Implement request validation schemas
    - Create backend/app/schemas/ with Pydantic models for all API requests
    - Define ChatMessageRequest with conversation_id, content validation
    - Define validation for message length (max 4096 chars)
    - Implement custom validators for input sanitization
    - _Requirements: 16.1, 16.2, 16.3, 16.4_
  
  - [ ]* 3.4 Write property tests for request validation
    - **Property 35: Missing fields return 422**
    - **Property 36: Invalid types return 422**
    - **Property 60: Message length is validated**
    - **Property 61: User input is sanitized**
    - _Requirements: 8.1, 16.1, 16.2, 16.3, 16.4_

- [ ] 4. Backend Database Service
  - [x] 4.1 Implement Supabase client wrapper
    - Create backend/app/services/db/supabase_client.py
    - Initialize Supabase client with credentials from environment
    - Implement user authentication methods
    - Implement conversation CRUD operations
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 7.1, 7.2_
  
  - [x] 4.2 Implement message persistence service
    - Create methods to save user messages with metadata (user_id, conversation_id, role, content, timestamp)
    - Create methods to save agent responses with same metadata
    - Implement message retrieval for conversation history
    - Ensure all queries respect user_id for isolation
    - _Requirements: 6.1, 6.2, 6.3, 6.5_
  
  - [ ]* 4.3 Write property tests for database operations
    - **Property 25: Messages are saved with correct metadata**
    - **Property 26: Agent responses are saved with correct metadata**
    - **Property 27: Conversation history is retrieved correctly**
    - **Property 28: New conversations are created correctly**
    - **Property 30: Users only see their own data**
    - **Property 31: User B cannot see User A's conversations**
    - **Property 34: RLS prevents unauthorized database access**
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.5_

- [ ] 5. Backend Tool Services
  - [x] 5.1 Implement Tavily search wrapper
    - Create backend/app/services/tools/tavily.py
    - Implement search method that calls Tavily API with query
    - Parse search results and return structured format
    - Implement error handling and logging
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [ ]* 5.2 Write property tests for Tavily search
    - **Property 17: Tavily search calls API correctly**
    - **Property 18: Tavily results are parsed correctly**
    - **Property 19: Tavily failures are handled**
    - **Property 20: Empty Tavily results are handled**
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [x] 5.3 Implement Google Trends MCP client wrapper
    - Create backend/app/services/tools/google_trends_mcp.py
    - Implement MCP client that communicates with external MCP server via Docker network
    - Use service name "mcp" instead of localhost
    - Implement timeout handling (default 10s)
    - Implement error handling and logging
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 10.2, 10.3_
  
  - [ ]* 5.4 Write property tests for Google Trends MCP
    - **Property 21: MCP communicates via Docker network**
    - **Property 22: MCP data is parsed correctly**
    - **Property 23: MCP unavailability is handled gracefully**
    - **Property 24: MCP timeouts are handled**
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 10.2, 10.3_

- [ ] 6. Backend ReAct Agent Service
  - [x] 6.1 Implement ReAct agent initialization
    - Create backend/app/services/agent/react_agent.py
    - Initialize LangChain ReAct agent with Tavily and MCP tools
    - Configure agent with system prompt for tool selection
    - Set iteration limit to 10
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6_
  
  - [x] 6.2 Implement agent message processing
    - Implement method to load conversation history from database
    - Format history as LangChain Message objects
    - Pass history to agent context
    - Implement agent invocation with user message
    - _Requirements: 6.5, 3.4_
  
  - [x] 6.3 Implement agent streaming response generation
    - Implement method to stream agent response tokens
    - Yield tokens as they are generated
    - Emit tool activity events when tools are invoked
    - Handle agent errors and provide fallback responses
    - _Requirements: 2.2, 2.3, 2.4, 3.5, 15.1_
  
  - [ ]* 6.4 Write property tests for ReAct agent
    - **Property 12: Trends queries invoke Google Trends MCP**
    - **Property 13: Web queries invoke Tavily Search**
    - **Property 14: Agent waits for tool responses**
    - **Property 15: Tool errors are handled gracefully**
    - **Property 16: Iteration limit stops reasoning**
    - **Property 29: Agent context includes conversation history**
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 6.5_

- [ ] 7. Backend Chat Router and SSE Streaming
  - [x] 7.1 Implement chat message endpoint with SSE streaming
    - Create backend/app/routers/chat.py with POST /chat/message endpoint
    - Validate request and extract user_id from token
    - Save user message to database
    - Establish SSE connection
    - Stream agent response tokens
    - Emit tool activity events
    - Save agent response to database
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 8.1, 8.2, 8.3, 8.4_
  
  - [x] 7.2 Implement conversation retrieval endpoints
    - Implement GET /chat/conversations to list user's conversations
    - Implement GET /chat/conversations/{id}/messages to get conversation messages
    - Ensure all queries respect user_id for isolation
    - _Requirements: 6.3, 7.1, 7.2_
  
  - [ ]* 7.3 Write property tests for chat streaming
    - **Property 7: User messages appear immediately**
    - **Property 8: Agent responses stream incrementally**
    - **Property 9: Tool activity indicators display during tool use**
    - **Property 10: Tool indicators clear after completion**
    - **Property 37: SSE connection streams tokens**
    - **Property 38: Tool activity events are emitted**
    - **Property 39: SSE connection closes after response**
    - **Property 40: Client disconnect triggers cleanup**
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 8. Backend Logging and Error Handling
  - [x] 8.1 Implement request-scoped logging
    - Create backend/app/utils/logging.py with request_id generation
    - Implement logging middleware that adds user_id and request_id to all logs
    - Ensure API keys and tokens are not logged
    - _Requirements: 12.1, 17.1, 17.2, 17.3, 17.4_
  
  - [x] 8.2 Implement error handling and response formatting
    - Create backend/app/utils/errors.py with custom exception classes
    - Implement error response formatting that doesn't expose stack traces
    - Implement error handlers for all exception types
    - _Requirements: 12.2, 15.1, 15.3, 15.4, 15.5_
  
  - [ ]* 8.3 Write property tests for logging and error handling
    - **Property 49: API keys not logged**
    - **Property 50: Stack traces not exposed to client**
    - **Property 57: Database unavailability doesn't crash backend**
    - **Property 58: Request timeout cancels operation**
    - **Property 59: Unexpected errors return generic message**
    - **Property 62: Tool invocations are logged**
    - **Property 63: Tool completions are logged**
    - **Property 64: Tool errors are logged internally**
    - **Property 65: Logs include user_id and request_id**
    - _Requirements: 12.1, 12.2, 15.1, 15.3, 15.4, 15.5, 17.1, 17.2, 17.3, 17.4_

- [ ] 9. Backend Checkpoint - Ensure all tests pass
  - Ensure all backend unit tests pass
  - Ensure all backend property tests pass (minimum 100 iterations each)
  - Verify no API keys or secrets in logs
  - Verify error responses don't expose internal details

- [ ] 10. Frontend Authentication Pages
  - [x] 10.1 Create login page component
    - Create frontend/src/pages/Login.tsx
    - Implement email and password input fields
    - Implement login form submission
    - Call backend /auth/login endpoint
    - Store token in localStorage
    - Redirect to chat on success
    - Display error messages on failure
    - _Requirements: 1.2, 1.3, 1.4_
  
  - [x] 10.2 Create signup page component
    - Create frontend/src/pages/Signup.tsx
    - Implement email, password, and confirm password input fields
    - Implement signup form submission
    - Call backend /auth/signup endpoint
    - Store token in localStorage
    - Redirect to chat on success
    - Display error messages on failure
    - _Requirements: 1.1, 1.4_
  
  - [ ]* 10.3 Write property tests for authentication pages
    - **Property 1: Signup creates user and returns token**
    - **Property 2: Login with valid credentials returns token**
    - **Property 3: Login with invalid credentials is rejected**
    - **Property 4: Token enables chat access**
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 11. Frontend API Client
  - [x] 11.1 Implement API client with token management
    - Create frontend/src/api/chatClient.ts
    - Implement token retrieval from localStorage
    - Implement token injection into request headers
    - Implement token refresh on 401 response
    - _Requirements: 1.4, 1.5_
  
  - [x] 11.2 Implement SSE connection management
    - Implement method to establish SSE connection to /chat/message endpoint
    - Implement token streaming handler
    - Implement tool activity event handler
    - Implement error handling and reconnection logic
    - _Requirements: 2.2, 2.3, 8.2, 8.3_
  
  - [x] 11.3 Implement conversation and message retrieval
    - Implement method to fetch user's conversations
    - Implement method to fetch messages for a conversation
    - Implement error handling
    - _Requirements: 2.5, 6.3_

- [ ] 12. Frontend Chat Interface
  - [x] 12.1 Create chat page component
    - Create frontend/src/pages/Chat.tsx
    - Implement message list display
    - Implement message input field
    - Implement send button
    - Load conversation history on page load
    - _Requirements: 2.1, 2.5, 6.3_
  
  - [x] 12.2 Create message component
    - Create frontend/src/components/Message.tsx
    - Implement user message display
    - Implement agent message display with streaming token support
    - Implement tool activity indicator display
    - Implement timestamp display
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [x] 12.3 Implement streaming token display
    - Implement incremental token rendering as they arrive via SSE
    - Implement tool activity indicator updates
    - Implement auto-scroll to latest message
    - _Requirements: 2.2, 2.3, 2.4_
  
  - [ ]* 12.4 Write property tests for chat interface
    - **Property 7: User messages appear immediately**
    - **Property 8: Agent responses stream incrementally**
    - **Property 9: Tool activity indicators display during tool use**
    - **Property 10: Tool indicators clear after completion**
    - **Property 11: Chat history persists and restores**
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.3_

- [ ] 13. Frontend State Management
  - [x] 13.1 Implement authentication state management
    - Create frontend/src/state/authContext.ts
    - Implement token storage and retrieval
    - Implement login/logout state management
    - Implement token expiration handling
    - _Requirements: 1.4, 1.5, 1.6_
  
  - [x] 13.2 Implement chat state management
    - Create frontend/src/state/chatContext.ts
    - Implement conversation state
    - Implement message list state
    - Implement loading and error states
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 14. Frontend Checkpoint - Ensure all tests pass
  - Ensure all frontend unit tests pass
  - Ensure all frontend property tests pass (minimum 100 iterations each)
  - Verify no API keys or secrets in client code
  - Verify chat history restores correctly on page reload

- [ ] 15. Docker Configuration
  - [x] 15.1 Create backend Dockerfile
    - Create backend/Dockerfile with Python base image
    - Install dependencies from requirements.txt
    - Copy application code
    - Expose port 8000
    - Set health check
    - _Requirements: 14.1, 14.2_
  
  - [x] 15.2 Create frontend Dockerfile
    - Create frontend/Dockerfile with Node base image
    - Install dependencies from package.json
    - Build React application
    - Serve with nginx or similar
    - Expose port 3000
    - Set health check
    - _Requirements: 13.1, 13.2_
  
  - [x] 15.3 Create docker-compose.yml
    - Define frontend service (port 3000)
    - Define backend service (port 8000)
    - Define MCP service (port 5000, external container)
    - Define Supabase service (or use managed service)
    - Configure environment variables for all services
    - Configure health checks for all services
    - Configure service dependencies
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ]* 15.4 Write property tests for Docker configuration
    - **Property 44: Docker Compose starts all services**
    - **Property 45: Services communicate via Docker network**
    - **Property 46: Health checks verify readiness**
    - **Property 48: Docker Compose waits for health checks**
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 16. Environment Configuration
  - [x] 16.1 Create .env.example files
    - Create root/.env.example with all required variables
    - Create backend/.env.example with backend-specific variables
    - Create frontend/.env.example with frontend-specific variables
    - Document all variables with descriptions
    - _Requirements: 12.3, 13.3, 13.4, 14.3, 14.4_
  
  - [x] 16.2 Verify no hardcoded localhost addresses
    - Search codebase for "localhost" references
    - Replace with environment variables or service names
    - Verify all service URLs use Docker service names
    - _Requirements: 10.3, 13.4, 14.4_
  
  - [ ]* 16.3 Write property tests for configuration
    - **Property 45: Services communicate via Docker network**
    - **Property 54: Frontend uses environment variables for backend URL**
    - **Property 56: Backend uses environment variables for service URLs**
    - _Requirements: 10.2, 10.3, 13.3, 13.4, 14.3, 14.4_

- [ ] 17. Integration Testing
  - [x] 17.1 Test end-to-end authentication flow
    - Test signup → login → chat access
    - Test token expiration and refresh
    - Test logout
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
  
  - [x] 17.2 Test end-to-end chat flow
    - Test sending message → agent response → message saved
    - Test streaming response display
    - Test tool activity indicators
    - Test chat history restoration
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.3_
  
  - [x] 17.3 Test tool integration
    - Test Tavily search invocation and result display
    - Test Google Trends MCP invocation and result display
    - Test tool error handling
    - Test MCP unavailability handling
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4_
  
  - [x] 17.4 Test user isolation
    - Test User A cannot see User B's conversations
    - Test RLS policies prevent cross-user access
    - Test 403 response for unauthorized access
    - _Requirements: 7.1, 7.2, 7.4, 7.5_
  
  - [x] 17.5 Test error handling and graceful degradation
    - Test MCP unavailability → friendly error message
    - Test database unavailability → error message, no crash
    - Test tool timeout → cancellation and user notification
    - Test invalid input → 422 response
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 18. Documentation and Deployment
  - [x] 18.1 Create comprehensive README.md
    - Document system architecture
    - Document setup instructions
    - Document environment variables
    - Document API endpoints
    - Document testing instructions
    - _Requirements: 10.1_
  
  - [x] 18.2 Create API documentation
    - Document all endpoints with request/response examples
    - Document authentication requirements
    - Document error responses
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_
  
  - [x] 18.3 Verify one-command startup
    - Test `docker compose up --build` starts all services
    - Verify all services are healthy
    - Verify frontend is accessible at localhost:3000
    - Verify backend is accessible at localhost:8000
    - _Requirements: 10.1, 10.4, 10.5_

- [x] 19. Final Checkpoint - Ensure all tests pass
  - Ensure all unit tests pass
  - Ensure all property tests pass (minimum 100 iterations each)
  - Ensure all integration tests pass
  - Verify Docker Compose startup works
  - Verify no secrets in logs or client code
  - Verify error responses are user-friendly

## Notes

- Tasks marked with `*` are optional test-related tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- All tests should run with minimum 100 iterations for property-based tests
- Docker Compose should start all services with a single command
- No localhost hardcoding in any configuration or code
- All API keys and secrets should be in .env files, not in code
- Error responses should be user-friendly and not expose internal details

