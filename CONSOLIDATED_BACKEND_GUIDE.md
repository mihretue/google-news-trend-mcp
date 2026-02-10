# Consolidated Backend Guide

## Overview

The backend has been consolidated into the existing `google-news-trends-mcp` folder. This single FastAPI server now provides:

1. **MCP Server** - Google News and Trends tools via `/mcp` endpoint
2. **Chatbot Backend** - Authentication, chat, and health endpoints
3. **ReAct Agent** - LangChain agent for intelligent tool selection
4. **Supabase Integration** - User authentication and chat persistence

## Project Structure

```
google-news-trends-mcp/
├── main.py                    # FastAPI app with all routers
├── mcp_server.py             # MCP server configuration
├── tools.py                  # MCP tools (news, trends)
├── auth.py                   # JWT authentication
├── chatbot_routers.py        # NEW: Chat, auth, health endpoints
├── supabase_client.py        # NEW: Supabase integration
├── react_agent.py            # NEW: LangChain ReAct agent
├── load_var.py               # Environment loading
├── pyproject.toml            # Updated with chatbot deps
├── Dockerfile                # Container config
├── security/                 # Security utilities
└── README.md                 # Documentation
```

## New Files Added

### 1. chatbot_routers.py
Contains all chatbot endpoints:
- **Authentication**: `/auth/signup`, `/auth/login`, `/auth/logout`
- **Chat**: `/chat/message`, `/chat/conversations`, `/chat/conversations/{id}/messages`
- **Health**: `/health`, `/health/ready`, `/health/live`

### 2. supabase_client.py
Handles all database operations:
- User authentication
- Conversation management
- Message persistence
- Health checks

### 3. react_agent.py
LangChain ReAct agent:
- Tool selection logic
- Message processing
- Streaming response generation
- Conversation history loading

## API Endpoints

### Authentication
```
POST /auth/signup
POST /auth/login
POST /auth/logout
```

### Chat
```
POST /chat/message (SSE streaming)
POST /chat/conversations
GET /chat/conversations
GET /chat/conversations/{id}/messages
```

### Health
```
GET /health
GET /health/ready
GET /health/live
GET /healthz (MCP health)
```

### MCP
```
POST /mcp (MCP protocol)
```

## Environment Variables

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# OpenAI (for LangChain)
OPENAI_API_KEY=your-openai-key

# Tavily (optional)
TAVILY_API_KEY=your-tavily-key

# Agent Configuration
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT=30

# MCP JWT (if using JWT auth)
MCP_JWT_ISSUER=your-issuer
MCP_JWT_AUDIENCE=your-audience
MCP_JWT_PUBLIC_KEY=your-public-key
```

## Running Locally

### 1. Install Dependencies
```bash
cd google-news-trends-mcp
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Set Environment Variables
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access Services
- API Docs: http://localhost:8000/docs
- MCP: http://localhost:8000/mcp
- Health: http://localhost:8000/health

## Docker Setup

### Build Image
```bash
docker build -t google-news-trends-mcp:latest .
```

### Run Container
```bash
docker run -p 8000:8000 \
  -e SUPABASE_URL=your-url \
  -e SUPABASE_KEY=your-key \
  -e SUPABASE_JWT_SECRET=your-secret \
  -e OPENAI_API_KEY=your-key \
  google-news-trends-mcp:latest
```

## Docker Compose Integration

The `docker-compose.yml` now uses the consolidated backend:

```yaml
backend:
  build:
    context: ./google-news-trends-mcp
    dockerfile: Dockerfile
  ports:
    - "8000:8000"
  environment:
    - SUPABASE_URL=${SUPABASE_URL}
    - SUPABASE_KEY=${SUPABASE_KEY}
    - SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET}
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - TAVILY_API_KEY=${TAVILY_API_KEY}
  depends_on:
    - mcp
  networks:
    - chatbot-network
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 10s
    timeout: 5s
    retries: 3
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────────────────────────────────┐ │
│  │   Frontend   │  │  Google News Trends MCP + Chatbot        │ │
│  │   (React)    │  │  ┌────────────────────────────────────┐  │ │
│  │   :3000      │  │  │ FastAPI Server (:8000)             │  │ │
│  └──────────────┘  │  │ ├─ /mcp (MCP tools)                │  │ │
│         │          │  │ ├─ /auth (Authentication)          │  │ │
│         │          │  │ ├─ /chat (Chat endpoints)          │  │ │
│         │          │  │ └─ /health (Health checks)         │  │ │
│         │          │  │                                    │  │ │
│         │          │  │ Components:                        │  │ │
│         │          │  │ ├─ MCP Server (news/trends)        │  │ │
│         │          │  │ ├─ ReAct Agent (LangChain)         │  │ │
│         │          │  │ ├─ Supabase Client (DB)            │  │ │
│         │          │  │ └─ JWT Auth Middleware             │  │ │
│         │          │  └────────────────────────────────────┘  │ │
│         │          └──────────────────────────────────────────┘ │
│         │                                                        │
│         └────────────────────────────────────────────────────┐  │
│                                                              │  │
│                    ┌───────────────────┐  ┌──────────────┐  │  │
│                    │   Supabase        │  │   Tavily     │  │  │
│                    │   (Auth + DB)     │  │   (External) │  │  │
│                    └───────────────────┘  └──────────────┘  │  │
│                                                              │  │
└─────────────────────────────────────────────────────────────┘  │
```

## Key Features

### 1. Unified Server
- Single FastAPI instance serving both MCP and chatbot
- Shared authentication and middleware
- Efficient resource usage

### 2. Tool Integration
- MCP tools (news, trends) available to ReAct agent
- Tavily search integration
- Intelligent tool selection

### 3. Chat Persistence
- Supabase for user authentication
- Message history storage
- Conversation management
- Row-Level Security for data isolation

### 4. Streaming Responses
- SSE (Server-Sent Events) for real-time streaming
- Token-by-token response delivery
- Tool activity indicators

### 5. Health Monitoring
- Service health checks
- Dependency status monitoring
- Readiness probes for orchestration

## Migration from Separate Backend

If you had the separate `backend/` folder, here's what changed:

**Before:**
```
backend/
├── app/
│   ├── main.py
│   ├── routers/
│   ├── services/
│   └── middleware/
frontend/
google-news-trends-mcp/
```

**After:**
```
google-news-trends-mcp/
├── main.py (consolidated)
├── chatbot_routers.py (new)
├── supabase_client.py (new)
├── react_agent.py (new)
├── mcp_server.py (existing)
├── tools.py (existing)
└── ...
frontend/
```

## Deployment

### Local Development
```bash
cd google-news-trends-mcp
pip install -e .
uvicorn main:app --reload
```

### Docker
```bash
docker build -t google-news-trends-mcp:latest .
docker run -p 8000:8000 google-news-trends-mcp:latest
```

### Docker Compose
```bash
docker compose up --build
```

## Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### API Documentation
```
http://localhost:8000/docs
```

### MCP Tools
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"name": "get_trending_terms", "arguments": {"geo": "US"}}'
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
# Kill process
kill -9 <PID>
```

### Missing Dependencies
```bash
pip install -e .
```

### Environment Variables Not Loaded
```bash
# Make sure .env file exists
ls -la .env
# Check variables are set
echo $SUPABASE_URL
```

### Supabase Connection Failed
- Verify SUPABASE_URL and SUPABASE_KEY
- Check internet connectivity
- Verify Supabase project is active

## Next Steps

1. **Configure Supabase**
   - Create project
   - Run migrations
   - Set environment variables

2. **Configure OpenAI**
   - Get API key
   - Set OPENAI_API_KEY

3. **Start Services**
   - Run `docker compose up --build`
   - Access frontend at http://localhost:3000

4. **Test System**
   - Sign up / login
   - Send messages
   - Verify streaming works

## Files to Delete (Optional)

If you want to clean up the old separate backend folder:
```bash
rm -rf backend/
```

The consolidated backend in `google-news-trends-mcp/` replaces all functionality.

## Support

For issues or questions:
1. Check environment variables
2. Review logs: `docker compose logs backend`
3. Check health endpoint: `curl http://localhost:8000/health`
4. Review API docs: http://localhost:8000/docs
