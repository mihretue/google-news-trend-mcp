# LangChain ReAct Chatbot System

A full-stack LangChain ReAct chatbot with Google Trends MCP, Tavily web search, streaming responses, Supabase authentication, and Docker Compose orchestration.

## System Architecture

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

## Prerequisites

- Docker and Docker Compose
- Supabase account with project created
- Tavily API key
- Google Trends MCP container (pre-built or available locally)

## Setup Instructions

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repo-url>
cd langchain-react-chatbot

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# - SUPABASE_URL: Your Supabase project URL
# - SUPABASE_KEY: Your Supabase anon key
# - SUPABASE_JWT_SECRET: Your Supabase JWT secret
# - TAVILY_API_KEY: Your Tavily API key
```

### 2. Configure Supabase

1. Create a Supabase project at https://supabase.com
2. Run the SQL migrations in `backend/migrations/` to create tables and RLS policies
3. Copy your project credentials to `.env`

### 3. Start Services

```bash
# Build and start all services
docker compose up --build

# Services will be available at:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - MCP: http://localhost:5000
```

### 4. Verify Health

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# Check MCP
curl http://localhost:5000/health
```

## Project Structure

```
.
├── frontend/                    # React TypeScript frontend
│   ├── src/
│   │   ├── api/                # API client
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── state/              # State management
│   │   ├── types/              # TypeScript types
│   │   └── utils/              # Utilities
│   ├── Dockerfile
│   ├── package.json
│   └── .env.example
│
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── core/               # Core configuration
│   │   ├── middleware/         # Middleware
│   │   ├── routers/            # API routes
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   └── health.py
│   │   ├── schemas/            # Pydantic models
│   │   ├── services/           # Business logic
│   │   │   ├── agent/          # ReAct agent
│   │   │   ├── tools/          # Tool wrappers
│   │   │   │   ├── tavily.py
│   │   │   │   └── google_trends_mcp.py
│   │   │   └── db/             # Database service
│   │   └── utils/              # Utilities
│   ├── migrations/             # SQL migrations
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── docker-compose.yml          # Docker Compose config
├── .env.example                # Environment template
└── README.md                   # This file
```

## API Endpoints

### Authentication

- `POST /auth/signup` - Create new account
- `POST /auth/login` - Login with email/password
- `POST /auth/logout` - Logout

### Chat

- `POST /chat/message` - Send message (SSE streaming)
- `GET /chat/conversations` - List conversations
- `GET /chat/conversations/{id}/messages` - Get messages

### Health

- `GET /health` - Service health status

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://project.supabase.co` |
| `SUPABASE_KEY` | Supabase anon key | `eyJhbGc...` |
| `SUPABASE_JWT_SECRET` | JWT secret for token validation | `super-secret-key` |
| `TAVILY_API_KEY` | Tavily API key | `tvly-...` |
| `MCP_URL` | Google Trends MCP URL | `http://mcp:5000` |
| `REACT_APP_API_URL` | Backend API URL (frontend) | `http://localhost:8000` |
| `ENVIRONMENT` | Environment (production/development) | `production` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Testing

### Run All Tests

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd ../frontend
npm test
```

### Run Property-Based Tests

```bash
# Backend property tests
cd backend
pytest tests/properties/ -v

# Frontend property tests
cd ../frontend
npm run test:properties
```

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run locally (requires .env)
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run locally
npm start
```

## Troubleshooting

### Services won't start

1. Check Docker is running: `docker ps`
2. Check ports are available: `lsof -i :3000`, `lsof -i :8000`, `lsof -i :5000`
3. Check environment variables: `cat .env`
4. View logs: `docker compose logs -f`

### Health check failures

```bash
# Check backend health
docker compose exec backend curl http://localhost:8000/health

# Check MCP health
docker compose exec mcp curl http://localhost:5000/health

# View service logs
docker compose logs backend
docker compose logs mcp
```

### Database connection issues

1. Verify Supabase credentials in `.env`
2. Check Supabase project is active
3. Verify RLS policies are enabled
4. Check network connectivity: `docker compose exec backend curl https://your-project.supabase.co`

## Key Design Decisions

### Why SSE vs WebSocket?

SSE (Server-Sent Events) is chosen for streaming because:
- Simpler HTTP-based protocol
- Built-in automatic reconnection
- Sufficient for unidirectional (server → client) streaming
- Better error handling with standard HTTP semantics
- Easier debugging with standard tools

### Tool Selection Logic

The ReAct agent uses intent classification to decide between tools:
- **Trends queries** (keywords: trending, popular, viral) → Google Trends MCP
- **Web queries** (current info, news, recent events) → Tavily Search
- **General knowledge** → Direct LLM response

### Data Isolation

Supabase Row-Level Security (RLS) enforces user isolation at the database level:
- All queries automatically filtered by `auth.uid()`
- Users can only access their own conversations and messages
- Application-level checks provide defense-in-depth

## Support

For issues or questions, please refer to the design document at `.kiro/specs/langchain-react-chatbot/design.md` or requirements at `.kiro/specs/langchain-react-chatbot/requirements.md`.
