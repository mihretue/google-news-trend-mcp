# Setup Instructions - LangChain ReAct Chatbot

Complete step-by-step guide to set up and run the full-stack chatbot system.

## Prerequisites

- Docker and Docker Compose installed
- Supabase account (free tier available)
- OpenAI API key
- Tavily API key (free tier available)

## Step 1: Supabase Setup

### 1.1 Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Sign up or log in
3. Create a new project
4. Note your project URL and anon key

### 1.2 Create Database Tables
1. Go to SQL Editor in Supabase dashboard
2. Run the migration SQL from `backend/migrations/001_create_tables.sql`:

```sql
-- Users table (managed by Supabase Auth)
-- Conversations table
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

-- Messages table
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  tool_calls JSONB,
  created_at TIMESTAMP DEFAULT now()
);

-- Enable RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies for conversations
CREATE POLICY "Users can view their own conversations"
  ON conversations FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create conversations"
  ON conversations FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own conversations"
  ON conversations FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own conversations"
  ON conversations FOR DELETE
  USING (auth.uid() = user_id);

-- RLS Policies for messages
CREATE POLICY "Users can view messages in their conversations"
  ON messages FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert messages in their conversations"
  ON messages FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

### 1.3 Get JWT Secret
1. Go to Project Settings → API
2. Copy the `JWT Secret` (you'll need this for `SUPABASE_JWT_SECRET`)

## Step 2: API Keys

### 2.1 OpenAI API Key
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create API key
3. Copy the key (starts with `sk-`)

### 2.2 Tavily API Key
1. Go to [tavily.com](https://tavily.com)
2. Sign up for free tier
3. Get your API key from dashboard

## Step 3: Environment Configuration

### 3.1 Create .env file
```bash
cp .env.example .env
```

### 3.2 Edit .env with your credentials
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# OpenAI
OPENAI_API_KEY=sk-your-key

# Tavily
TAVILY_API_KEY=your-key

# MCP JWT (optional for local development)
MCP_JWT_ISSUER=https://issuer.example.com/
MCP_JWT_AUDIENCE=clickup-mcp
MCP_JWT_PUBLIC_KEY=your-public-key

# Agent
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT=30

# Server
PORT=8000
ENVIRONMENT=development
```

## Step 4: Run the System

### 4.1 Build and Start Services
```bash
docker compose up --build
```

This will:
- Build the frontend (React)
- Build the backend (FastAPI + MCP)
- Start both services
- Run health checks

### 4.2 Wait for Services to Start
```
frontend_1  | Accepting connections at http://localhost:3000
backend_1   | Uvicorn running on http://0.0.0.0:8000
```

### 4.3 Access the Application
- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Backend Health**: http://localhost:8000/health

## Step 5: Test the System

### 5.1 Create Account
1. Go to http://localhost:3000
2. Click "Sign Up"
3. Enter email and password (min 8 chars)
4. Click "Create Account"

### 5.2 Login
1. Enter your credentials
2. Click "Login"
3. You should be redirected to chat page

### 5.3 Test Chat
1. Type a message: "Hello"
2. You should see streaming response
3. Try: "Search the web for LangChain"
4. Try: "What are trending topics?"

### 5.4 Verify Features
- ✅ Messages appear in real-time (streaming)
- ✅ Tool activity indicators show (if tools are called)
- ✅ Chat history persists after refresh
- ✅ Can create multiple conversations

## Step 6: Troubleshooting

### Backend won't start
```bash
# Check logs
docker compose logs backend

# Common issues:
# - SUPABASE_URL or SUPABASE_KEY not set
# - OPENAI_API_KEY not set
# - Port 8000 already in use
```

### Frontend can't connect
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS headers
# Open browser DevTools → Network tab
# Look for CORS errors in console
```

### Chat not working
```bash
# Check JWT token is valid
# Open browser DevTools → Application → Local Storage
# Look for "auth_token"

# Check Supabase connection
# Backend logs should show database operations
docker compose logs backend | grep -i supabase
```

### Tool execution failing
```bash
# Check OpenAI API key is valid
# Check Tavily API key is valid
# View backend logs for tool errors
docker compose logs backend | grep -i tool
```

## Step 7: Development

### Local Development (without Docker)

#### Backend
```bash
cd google-news-trends-mcp
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

### Running Tests
```bash
# Backend tests
cd google-news-trends-mcp
pytest

# Frontend tests
cd frontend
npm test
```

## Step 8: Production Deployment

### 8.1 Update Environment
```bash
# Set production environment
ENVIRONMENT=production

# Use production Supabase project
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_KEY=prod-key

# Configure MCP JWT properly
MCP_JWT_ISSUER=your-issuer
MCP_JWT_PUBLIC_KEY=your-public-key
```

### 8.2 Build Images
```bash
docker compose build
```

### 8.3 Deploy
```bash
# Using Docker Compose
docker compose -f docker-compose.yml up -d

# Or push to container registry and deploy to cloud
docker tag frontend:latest your-registry/frontend:latest
docker push your-registry/frontend:latest
```

## Architecture Overview

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

## Key Features

✅ **Authentication**
- Email/password signup and login
- JWT token-based authorization
- Secure token storage

✅ **Chat**
- Real-time streaming responses
- Conversation history
- Message persistence

✅ **Tools**
- Google Trends integration
- Tavily web search
- Tool activity indicators

✅ **Security**
- Row-level security (RLS) in Supabase
- JWT validation on all protected endpoints
- CORS configuration
- No API keys exposed to frontend

✅ **Infrastructure**
- Docker containerization
- Docker Compose orchestration
- Health checks
- Graceful error handling

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review backend logs: `docker compose logs backend`
3. Review frontend console: Browser DevTools → Console
4. Check Supabase dashboard for database issues

## Next Steps

1. Customize the chatbot prompt in `google-news-trends-mcp/react_agent.py`
2. Add more tools to the agent
3. Implement conversation analytics
4. Add user preferences and settings
5. Deploy to production environment
