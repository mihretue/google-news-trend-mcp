# Quick Fix Reference - MCP 403 Error

## Problem
MCP service was returning 403 errors when backend tried to call it.

## Root Cause
Backend wasn't sending JWT authorization token to MCP service.

## Solution Applied

### 1. Backend Authorization Fix
**File:** `backend/app/services/tools/google_trends_mcp.py`

Added JWT token generation:
```python
def _create_mcp_token(self) -> str:
    payload = {"sub": "backend-service", "iat": int(time.time())}
    token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    return token
```

All MCP requests now include:
```python
headers = {"Authorization": f"Bearer {token}"}
response = await client.post(endpoint, json=payload, headers=headers)
```

### 2. Docker Environment Variables
**File:** `docker-compose.yml`

MCP service now gets Supabase credentials:
```yaml
mcp:
  environment:
    - SUPABASE_URL=${SUPABASE_URL}
    - SUPABASE_KEY=${SUPABASE_KEY}
    - SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET}
```

### 3. MCP Service Cleanup
**File:** `google-news-trends-mcp/main.py`

Removed unnecessary imports that were causing errors:
- ❌ Removed: `from chatbot_routers import ...`
- ❌ Removed: `from react_agent import ...`
- ✅ Kept: Just MCP server + health checks

## To Test

```bash
# Rebuild
docker compose down
docker compose up --build

# Wait for containers
docker ps  # Should show 3 containers

# Test in browser
# http://localhost:3000
# Ask: "What's trending?"
# Should see trending data (no 403)
```

## Expected Results

✅ **Trending queries** - Return actual trending data
⚠️ **Web search queries** - Return 403 (dev key), graceful fallback
✅ **General knowledge** - Work normally

## Files Changed

1. `backend/app/services/tools/google_trends_mcp.py` - JWT token generation
2. `docker-compose.yml` - Environment variables
3. `google-news-trends-mcp/main.py` - Simplified service

## Status

✅ Code fixes complete
⏳ Waiting for Docker build (network timeout earlier)

When network is stable, rebuild and test!
