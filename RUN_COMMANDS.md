# Run Commands - LangChain ReAct Chatbot

Quick reference for all commands needed to set up and run the system.

## Prerequisites Check

```bash
# Check Docker is installed
docker --version

# Check Docker Compose is installed
docker compose --version

# Check you have the required credentials:
# - Supabase URL and Key
# - OpenAI API Key
# - Tavily API Key
```

## Step 1: Supabase Setup

### Create Supabase Project
1. Go to https://supabase.com
2. Sign up or log in
3. Create new project
4. Copy: Project URL, Anon Key, JWT Secret

### Run Migrations
```bash
# In Supabase SQL Editor, run:
# Content from: backend/migrations/001_create_tables.sql

# Or copy-paste this:
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  tool_calls JSONB,
  created_at TIMESTAMP DEFAULT now()
);

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

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

CREATE POLICY "Users can view messages in their conversations"
  ON messages FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert messages in their conversations"
  ON messages FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

## Step 2: Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# On macOS/Linux:
nano .env

# On Windows:
notepad .env

# Required values to set:
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=your-anon-key
# SUPABASE_JWT_SECRET=your-jwt-secret
# OPENAI_API_KEY=sk-your-key
# TAVILY_API_KEY=your-key
```

## Step 3: Clean Up (Optional but Recommended)

```bash
# Delete the old separate backend folder (no longer needed)
rm -rf backend/
```

## Step 4: Build and Start

```bash
# Build and start all services
docker compose up --build

# Wait for output like:
# frontend_1  | Accepting connections at http://localhost:3000
# backend_1   | Uvicorn running on http://0.0.0.0:8000
```

## Step 5: Test the System

### In a new terminal:

```bash
# Test backend health
curl http://localhost:8000/health

# Test signup
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Test health check
curl http://localhost:8000/health | jq .

# View API documentation
# Open: http://localhost:8000/docs
```

## Step 6: Use the Application

```bash
# Open in browser
# Frontend: http://localhost:3000
# Backend API Docs: http://localhost:8000/docs
# Backend Health: http://localhost:8000/health
```

## Common Docker Commands

```bash
# View logs
docker compose logs

# View backend logs only
docker compose logs backend

# View frontend logs only
docker compose logs frontend

# Follow logs in real-time
docker compose logs -f

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v

# Rebuild services
docker compose build

# Rebuild and start
docker compose up --build

# Start in background
docker compose up -d

# Check service status
docker compose ps

# Execute command in backend
docker compose exec backend bash

# Execute command in frontend
docker compose exec frontend bash
```

## Development Commands

### Backend Development (without Docker)

```bash
# Navigate to backend
cd google-news-trends-mcp

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -e .

# Run development server
uvicorn main:app --reload

# Run tests
pytest

# Run with specific log level
uvicorn main:app --reload --log-level debug
```

### Frontend Development (without Docker)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build

# Run property-based tests
npm run test:properties
```

## Troubleshooting Commands

```bash
# Check if ports are in use
# On macOS/Linux:
lsof -i :3000
lsof -i :8000

# On Windows:
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Kill process on port (macOS/Linux)
kill -9 <PID>

# Kill process on port (Windows)
taskkill /PID <PID> /F

# Check Docker disk usage
docker system df

# Clean up Docker (remove unused images/containers)
docker system prune

# View Docker logs
docker logs <container-id>

# Inspect Docker network
docker network inspect chatbot-network

# Test Supabase connection
curl https://your-project.supabase.co/rest/v1/conversations \
  -H "apikey: your-anon-key" \
  -H "Authorization: Bearer your-token"
```

## Production Deployment

```bash
# Build production images
docker compose build

# Tag images for registry
docker tag frontend:latest your-registry/frontend:latest
docker tag google-news-trends-mcp:latest your-registry/backend:latest

# Push to registry
docker push your-registry/frontend:latest
docker push your-registry/backend:latest

# Deploy with production environment
docker compose -f docker-compose.yml up -d

# View production logs
docker compose logs -f

# Scale services (if using Swarm/Kubernetes)
docker service scale backend=3
```

## Monitoring Commands

```bash
# Check service health
curl http://localhost:8000/health

# Check readiness
curl http://localhost:8000/health/ready

# Check liveness
curl http://localhost:8000/health/live

# Monitor resource usage
docker stats

# View container processes
docker top <container-id>

# Inspect container
docker inspect <container-id>
```

## Database Commands

```bash
# Connect to Supabase database (if using psql)
psql "postgresql://postgres:password@db.supabase.co:5432/postgres"

# View conversations
SELECT * FROM conversations;

# View messages
SELECT * FROM messages;

# Count messages per user
SELECT user_id, COUNT(*) FROM messages GROUP BY user_id;

# Delete all messages for a user
DELETE FROM messages WHERE user_id = 'user-id';

# Delete all conversations for a user
DELETE FROM conversations WHERE user_id = 'user-id';
```

## Quick Reference

| Task | Command |
|------|---------|
| Start system | `docker compose up --build` |
| Stop system | `docker compose down` |
| View logs | `docker compose logs -f` |
| Test backend | `curl http://localhost:8000/health` |
| Test frontend | Open http://localhost:3000 |
| API docs | Open http://localhost:8000/docs |
| Backend shell | `docker compose exec backend bash` |
| Frontend shell | `docker compose exec frontend bash` |
| Clean up | `docker compose down -v` |
| Rebuild | `docker compose build --no-cache` |

## Environment Variables Reference

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# OpenAI
OPENAI_API_KEY=sk-your-key

# Tavily
TAVILY_API_KEY=your-key

# MCP JWT (optional)
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

## Useful Links

- Supabase: https://supabase.com
- OpenAI: https://platform.openai.com
- Tavily: https://tavily.com
- Docker: https://docker.com
- Docker Compose: https://docs.docker.com/compose/

---

**Ready to run!** 🚀

For detailed setup instructions, see `SETUP_INSTRUCTIONS.md`
For architecture details, see `SYSTEM_INTEGRATION_GUIDE.md`
