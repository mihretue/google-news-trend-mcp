# System Integration Guide - Consolidated Backend

## Overview

This document describes the consolidated system architecture where the `google-news-trends-mcp` folder serves as the single backend server for both MCP tools and chatbot functionality.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────────────┐  │
│  │   Frontend       │         │   Backend (MCP + Chat)   │  │
│  │  (React + TS)    │◄───────►│  (FastAPI)               │  │
│  │  Port: 3000      │         │  Port: 8000              │  │
│  └──────────────────┘         ├──────────────────────────┤  │
│                               │ /mcp - MCP tools         │  │
│                               │ /auth - Authentication   │  │
│                               │ /chat - Chat endpoints   │  │
│                               │ /health - Health checks  │  │
│                               └──────────────────────────┘  │
│                                        │                     │
│                                        ▼                     │
│                               ┌──────────────────┐           │
│                               │    Supabase      │           │
│                               │  (External)      │           │
│                               └──────────────────┘           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Services

### 1. Frontend (React + TypeScript)
- **Location**: `frontend/`
- **Port**: 3000
- **Dockerfile**: `frontend/Dockerfile`
- **Environment**: `REACT_APP_API_URL=http://backend:8000`
- **Features**:
  - Login/Signup pages
  - Chat interface with streaming support
  - Tool activity indicators
  - Message history

### 2. Backend (Consolidated MCP + Chatbot)
- **Location**: `google-news-trends-mcp/`
- **Port**: 8000
- **Dockerfile**: `google-news-trends-mcp/Dockerfile`
- **Main Entry**: `google-news-trends-mcp/main.py`

#### Backend Components:

**a) MCP Server** (`/mcp`)
- Google News tools
- Google Trends tools
- JWT authorization required
- Mounted at `/mcp` path

**b) Authentication Router** (`/auth`)
- `POST /auth/signup` - Create new user
- `POST /auth/login` - Authenticate user
- `POST /auth/logout` - Logout user
- Returns JWT token for subsequent requests

**c) Chat Router** (`/chat`)
- `POST /chat/conversations` - Create conversation
- `GET /chat/conversations` - List conversations
- `GET /chat/conversations/{id}/messages` - Get messages
- `POST /chat/message` - Send message (SSE streaming)
- Requires JWT authorization

**d) Health Router** (`/health`)
- `GET /health` - Full health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check

### 3. External Services
- **Supabase**: Database, authentication, RLS policies
- **OpenAI**: LLM for ReAct agent
- **Tavily**: Web search API

## Environment Variables

### Backend (.env)
```
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# OpenAI
OPENAI_API_KEY=sk-your-key

# Tavily
TAVILY_API_KEY=your-key

# MCP JWT
MCP_JWT_ISSUER=https://issuer.example.com/
MCP_JWT_AUDIENCE=clickup-mcp
MCP_JWT_PUBLIC_KEY=your-public-key

# Agent
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT=30

# Server
PORT=8000
ENVIRONMENT=production
```

### Frontend (.env)
```
REACT_APP_API_URL=http://backend:8000
```

## Docker Compose

The `docker-compose.yml` orchestrates both services:

```yaml
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on:
      backend: { condition: service_healthy }
    
  backend:
    build: ./google-news-trends-mcp
    ports: ["8000:8000"]
    environment: [all env vars]
    healthcheck: curl -f http://localhost:8000/healthz
```

**Key Changes from Previous Setup**:
- ✅ Backend builds from `google-news-trends-mcp/` (not separate `backend/`)
- ✅ No separate MCP service (integrated into backend)
- ✅ Single FastAPI app serves all endpoints
- ✅ Simplified networking (2 services instead of 3)

## API Endpoints

### Authentication
```
POST /auth/signup
  Body: { email, password }
  Response: { access_token, user_id, email }

POST /auth/login
  Body: { email, password }
  Response: { access_token, user_id, email }

POST /auth/logout
  Response: { message }
```

### Chat
```
POST /chat/conversations
  Headers: Authorization: Bearer <token>
  Body: { title }
  Response: { id, user_id, title, created_at }

GET /chat/conversations
  Headers: Authorization: Bearer <token>
  Response: { conversations: [...], count }

GET /chat/conversations/{id}/messages
  Headers: Authorization: Bearer <token>
  Response: { messages: [...], count }

POST /chat/message
  Headers: Authorization: Bearer <token>
  Body: { conversation_id, content }
  Response: SSE stream with events:
    - event: token, data: { token }
    - event: tool_activity, data: { tool, status }
    - event: done, data: { message_id }
    - event: error, data: { error }
```

### Health
```
GET /health
  Response: { status, services: { backend, supabase, mcp } }

GET /health/ready
  Response: { status, services }

GET /health/live
  Response: { status }

GET /healthz
  Response: "ok"
```

### MCP (Requires JWT)
```
POST /mcp
  Headers: Authorization: Bearer <jwt>
  Body: JSON-RPC payload
  Response: JSON-RPC response
```

## Data Flow

### 1. User Authentication
```
Frontend (Login) 
  → POST /auth/login 
  → Supabase Auth 
  → JWT Token 
  → Frontend stores token
```

### 2. Chat Message
```
Frontend (Send Message)
  → POST /chat/message (with JWT)
  → Backend validates JWT
  → Load conversation history from Supabase
  → Initialize ReAct agent
  → Agent selects tools (Tavily, Google Trends)
  → Stream response via SSE
  → Save message to Supabase
  → Frontend receives tokens and displays
```

### 3. Tool Execution
```
Agent (ReAct)
  → Analyze user message
  → Select tool (Tavily or Google Trends)
  → Execute tool
  → Stream tool_activity event
  → Process results
  → Generate response
  → Stream tokens
```

## Security

### JWT Validation
- All protected endpoints require `Authorization: Bearer <token>` header
- Token validated against `SUPABASE_JWT_SECRET`
- User ID extracted from token `sub` claim
- Attached to request state for authorization checks

### Supabase RLS
- Conversations table: Users can only access their own conversations
- Messages table: Users can only access messages in their conversations
- Enforced at database level

### CORS
- Frontend origin allowed: `http://localhost:3000`, `http://frontend:3000`
- Credentials enabled for cross-origin requests

## Running the System

### Local Development
```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your credentials

# 2. Start services
docker compose up --build

# 3. Access
Frontend: http://localhost:3000
Backend: http://localhost:8000
Docs: http://localhost:8000/docs
```

### Production
```bash
# Build images
docker compose build

# Run with production settings
docker compose -f docker-compose.yml up -d
```

## Troubleshooting

### Backend won't start
- Check `SUPABASE_URL` and `SUPABASE_KEY` are set
- Check `OPENAI_API_KEY` is set
- Check port 8000 is not in use
- View logs: `docker compose logs backend`

### Frontend can't connect to backend
- Check `REACT_APP_API_URL` is correct
- Check backend is healthy: `curl http://localhost:8000/health`
- Check CORS headers in browser console

### Chat not working
- Verify JWT token is valid
- Check Supabase tables exist and have RLS policies
- Check OpenAI API key is valid
- View backend logs for errors

### MCP tools not working
- Check MCP JWT configuration
- Verify tools are registered in `tools.py`
- Check tool implementations for errors

## Files Structure

```
.
├── docker-compose.yml          # Orchestration
├── .env.example                # Environment template
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── api/
│       │   ├── chatClient.ts   # API client
│       │   └── config.ts       # Endpoints
│       ├── pages/
│       │   ├── Login.tsx
│       │   ├── Signup.tsx
│       │   └── Chat.tsx
│       ├── components/
│       │   └── Message.tsx
│       ├── state/
│       │   ├── authContext.tsx
│       │   └── chatContext.tsx
│       └── styles/
│
└── google-news-trends-mcp/
    ├── Dockerfile
    ├── main.py                 # FastAPI app
    ├── mcp_server.py           # MCP setup
    ├── chatbot_routers.py      # Chat endpoints
    ├── auth.py                 # JWT validation
    ├── supabase_client.py      # DB client
    ├── react_agent.py          # LangChain agent
    ├── tools.py                # MCP tools
    ├── pyproject.toml
    └── .env.example
```

## Next Steps

1. **Set up Supabase**:
   - Create project
   - Run migrations from `backend/migrations/001_create_tables.sql`
   - Configure RLS policies

2. **Configure API Keys**:
   - OpenAI API key
   - Tavily API key
   - Supabase credentials

3. **Test System**:
   - Run `docker compose up --build`
   - Test signup/login
   - Test chat with streaming
   - Test tool execution

4. **Deploy**:
   - Push to production environment
   - Configure production environment variables
   - Set up monitoring and logging
