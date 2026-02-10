# Quick Start Guide

Get the LangChain ReAct Chatbot running in 5 minutes.

## Prerequisites
- Docker & Docker Compose
- Supabase account (free)
- OpenAI API key
- Tavily API key

## 1. Supabase Setup (2 min)

```bash
# 1. Create project at supabase.com
# 2. Copy your credentials:
#    - Project URL
#    - Anon Key
#    - JWT Secret

# 3. Run migrations in SQL Editor:
# Copy content from: backend/migrations/001_create_tables.sql
```

## 2. Environment Setup (1 min)

```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials:
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=your-anon-key
# SUPABASE_JWT_SECRET=your-jwt-secret
# OPENAI_API_KEY=sk-your-key
# TAVILY_API_KEY=your-key
```

## 3. Start System (1 min)

```bash
docker compose up --build
```

Wait for:
```
frontend_1  | Accepting connections at http://localhost:3000
backend_1   | Uvicorn running on http://0.0.0.0:8000
```

## 4. Test (1 min)

1. Open http://localhost:3000
2. Sign up with email/password
3. Type: "Hello"
4. See streaming response ✅

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/signup` | POST | Create account |
| `/auth/login` | POST | Login |
| `/chat/conversations` | GET/POST | Manage conversations |
| `/chat/message` | POST | Send message (SSE) |
| `/health` | GET | Health check |
| `/docs` | GET | API documentation |

## Troubleshooting

**Backend won't start**
```bash
docker compose logs backend
# Check: SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY
```

**Frontend can't connect**
```bash
curl http://localhost:8000/health
# Check: CORS, backend running
```

**Chat not working**
```bash
# Check browser console for errors
# Check backend logs: docker compose logs backend
```

## Architecture

```
Frontend (3000) ←→ Backend (8000) ←→ Supabase
                        ↓
                   MCP Tools
                   ReAct Agent
```

## Key Files

- `docker-compose.yml` - Orchestration
- `google-news-trends-mcp/` - Backend
- `frontend/` - React app
- `.env` - Configuration

## Next Steps

1. Customize agent prompt in `google-news-trends-mcp/react_agent.py`
2. Add more tools
3. Deploy to production
4. Set up monitoring

## Full Documentation

- **Setup**: See `SETUP_INSTRUCTIONS.md`
- **Architecture**: See `SYSTEM_INTEGRATION_GUIDE.md`
- **Status**: See `CONSOLIDATION_COMPLETE.md`

---

**Ready to go!** 🚀
