# Why You Were Getting 403 Errors

## The Problem

When you asked the chatbot "What's trending?" from the browser, you got a 403 error. This wasn't a browser issue—it was a backend-to-MCP communication issue.

## What Was Happening

### The Flow (Before Fix)

```
Browser (http://localhost:3000)
    ↓
Frontend (React)
    ↓
Backend (FastAPI) at http://localhost:8000
    ↓
MCP Service at http://mcp:5000
    ↓
MCP Authorization Middleware
    ↓
❌ 403 Unauthorized (missing Authorization header)
```

### Why 403?

The MCP service has **JWT authorization middleware** that checks every incoming request for a valid Bearer token in the Authorization header.

**MCP's auth.py:**
```python
def check_authorization(headers) -> str:
    auth = headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise UnauthorizedError("Authorization header missing or invalid")
    # ... validate token ...
```

### What the Backend Was Doing

The backend's `google_trends_mcp.py` was making HTTP requests like this:

```python
async with httpx.AsyncClient(timeout=self.timeout) as client:
    response = await client.post(
        "http://mcp:5000/mcp/tools/call",
        json=payload
        # ❌ NO Authorization header!
    )
```

**Result:** MCP middleware rejects the request → 403 Unauthorized

## The Solution

### What We Fixed

Updated the backend to create a JWT token and include it in every request:

```python
def _create_mcp_token(self) -> str:
    """Create a JWT token for MCP authorization."""
    payload = {
        "sub": "backend-service",
        "iat": int(time.time()),
    }
    token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    return token

async def get_trending_terms(self, geo: str = "US"):
    token = self._create_mcp_token()
    
    headers = {
        "Authorization": f"Bearer {token}",  # ✅ Now included!
        "Content-Type": "application/json",
    }
    
    response = await client.post(
        "http://mcp:5000/mcp/tools/call",
        json=payload,
        headers=headers  # ✅ Pass headers
    )
```

### How It Works Now

```
Backend creates JWT token
    ↓
Signs with Supabase JWT secret (same secret MCP uses)
    ↓
Includes in Authorization header: "Bearer {token}"
    ↓
Sends to MCP
    ↓
MCP middleware validates token
    ↓
✅ 200 OK - Request allowed
    ↓
MCP returns trending data
    ↓
Backend sends to frontend
    ↓
Frontend displays to user
```

## Why This Works

1. **Same Secret** - Backend and MCP both use `SUPABASE_JWT_SECRET`
2. **Same Algorithm** - Both use HS256 for signing
3. **Valid Claims** - Token includes `sub: "backend-service"` claim
4. **Proper Format** - Token sent as `Bearer {token}` in Authorization header

## The Two 403 Errors You Were Seeing

### 1. MCP 403 (Now Fixed)
- **Cause:** Missing Authorization header
- **Solution:** Added JWT token generation and header
- **Status:** ✅ FIXED

### 2. Tavily 403 (Expected)
- **Cause:** Dev API key has limitations
- **Solution:** Get production key from https://tavily.com
- **Status:** ⚠️ Gracefully handled (falls back to LLM knowledge)

## Verification

After the fix, you should see in backend logs:

```
INFO: Fetching trending terms for geo=US
INFO: Trending terms fetched successfully
```

Instead of:

```
ERROR: MCP HTTP error: 403 Client Error: Forbidden
```

## Files Changed

- `backend/app/services/tools/google_trends_mcp.py`
  - Added `_create_mcp_token()` method
  - Updated `get_trending_terms()` to include auth header
  - Updated `get_news_by_keyword()` to include auth header
  - Updated `health_check()` to include auth header

## No Changes Needed

- MCP service (already has auth middleware)
- Frontend (doesn't need to know about this)
- Docker Compose (already correct)
- Environment variables (already configured)

## Testing

```bash
# Rebuild
docker compose down
docker compose up --build

# Test in browser
# Ask: "What's trending?"
# Should see trending data, no 403 error
```

## Summary

The 403 error was happening because the backend wasn't sending the required JWT authorization token to the MCP service. We fixed it by:

1. Creating a JWT token using the shared Supabase secret
2. Including the token in the Authorization header
3. Sending it with every request to MCP

Now the MCP service recognizes the backend as authorized and returns the trending data successfully.
