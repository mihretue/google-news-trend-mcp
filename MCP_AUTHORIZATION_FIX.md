# MCP Authorization Fix

## Problem
The MCP service was returning 403 errors when the backend tried to call it. This was because the MCP server has JWT authorization middleware that requires a Bearer token in the Authorization header.

## Root Cause
The `backend/app/services/tools/google_trends_mcp.py` was making HTTP requests to the MCP service without including the required Authorization header with a JWT token.

## Solution
Updated `google_trends_mcp.py` to:

1. **Create JWT tokens** - Added `_create_mcp_token()` method that generates a JWT token signed with the Supabase JWT secret
2. **Include Authorization header** - All HTTP requests to MCP now include `Authorization: Bearer {token}` header
3. **Apply to all methods**:
   - `get_trending_terms()` - Now includes auth header
   - `get_news_by_keyword()` - Now includes auth header
   - `health_check()` - Now includes auth header

## Changes Made

### File: `backend/app/services/tools/google_trends_mcp.py`

**Added imports:**
```python
from jose import jwt
import os
```

**Added method:**
```python
def _create_mcp_token(self) -> str:
    """Create a JWT token for MCP authorization."""
    try:
        payload = {
            "sub": "backend-service",
            "iat": int(__import__('time').time()),
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token
    except Exception as e:
        logger.error(f"Failed to create MCP token: {str(e)}")
        return ""
```

**Updated all HTTP requests to include:**
```python
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}
response = await client.post(endpoint, json=payload, headers=headers)
```

## How It Works

1. Backend creates a JWT token using the Supabase JWT secret
2. Token is signed with algorithm HS256 (same as MCP expects)
3. Token includes `sub: "backend-service"` claim
4. Token is sent in Authorization header as Bearer token
5. MCP middleware validates the token and allows the request

## Testing

After rebuilding:

```bash
# Rebuild containers
docker compose down
docker compose up --build

# Test in browser
# 1. Go to http://localhost:3000
# 2. Login
# 3. Ask: "What's trending?"
# 4. Should see trending data (no 403 error)
```

## Expected Behavior

**Before fix:**
- Browser → Frontend → Backend → MCP
- MCP returns 403 (Unauthorized)
- Backend returns error to frontend
- User sees "Trends service unavailable"

**After fix:**
- Browser → Frontend → Backend → MCP
- Backend includes JWT token in request
- MCP validates token and returns 200 OK
- Backend gets trending data
- User sees actual trending topics

## Tavily 403 Note

The Tavily 403 error is separate and expected with a dev API key. This is handled gracefully by the agent which falls back to LLM knowledge. To fix Tavily:

1. Get a production key from https://tavily.com
2. Update `backend/.env`: `TAVILY_API_KEY=your_production_key`
3. Restart: `docker compose restart backend`

## Files Modified

- `backend/app/services/tools/google_trends_mcp.py` - Added JWT token generation and authorization headers

## No Changes Needed

- `backend/requirements.txt` - Already has `python-jose[cryptography]`
- `backend/app/core/config.py` - Already has `supabase_jwt_secret`
- `docker-compose.yml` - Already correct
- `backend/.env` - Already has `SUPABASE_JWT_SECRET`
