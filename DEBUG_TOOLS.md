# Debug Both Tools - Step by Step

## Prerequisites

1. **Start Docker Desktop** - Make sure it's running
2. **Start containers** - Run: `docker compose up --build`
3. **Wait for startup** - Give it 30 seconds to fully start

## Step 1: Check Container Status

```bash
docker ps
```

You should see:
- ✅ backend (port 8000)
- ✅ frontend (port 3000)
- ✅ mcp (port 5000)

If any are missing, restart:
```bash
docker compose down
docker compose up --build
```

## Step 2: Check Backend Logs

```bash
docker logs backend -f
```

Look for:
- ✅ "Application startup complete"
- ✅ "Uvicorn running on 0.0.0.0:8000"

If you see errors, note them.

## Step 3: Test MCP Connectivity

```bash
curl http://localhost:5000/healthz
```

Expected response:
```
200 OK
```

If fails:
- ❌ MCP container not running
- ❌ Port 5000 not exposed
- ❌ MCP service crashed

## Step 4: Test Tavily API Directly

```bash
python -c "
from tavily import TavilyClient
client = TavilyClient(api_key='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')
result = client.search('LangChain', max_results=3)
print('Tavily works:', result)
"
```

Expected: Search results or error message

If fails:
- ❌ Tavily API key invalid
- ❌ Tavily API down
- ❌ Network issue

## Step 5: Test Backend API

```bash
# Get health status
curl http://localhost:8000/health
```

Expected:
```json
{"status": "ok"}
```

## Step 6: Test Tool Invocation via Backend

Create a test file `test_tools_direct.py`:

```python
import asyncio
import sys
sys.path.insert(0, 'backend')

from app.services.tools.tavily import tavily_tool
from app.services.tools.google_trends_mcp import google_trends_tool

async def test_tools():
    print("=" * 60)
    print("Testing Tavily Search")
    print("=" * 60)
    
    try:
        result = await tavily_tool.search("LangChain agents", max_results=3)
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Results: {len(result['results'])} found")
            print(f"Answer: {result['answer'][:100]}...")
        else:
            print(f"Error: {result['error']}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Testing Google Trends MCP")
    print("=" * 60)
    
    try:
        result = await google_trends_tool.get_trending_terms()
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Trends: {result['trends'][:3]}")
        else:
            print(f"Error: {result['error']}")
    except Exception as e:
        print(f"Exception: {str(e)}")

asyncio.run(test_tools())
```

Run it:
```bash
cd backend
python ../test_tools_direct.py
```

## Step 7: Check Backend Logs for Tool Errors

```bash
docker logs backend | grep -i "tavily\|mcp\|tool"
```

Look for:
- Tool invocation attempts
- Error messages
- Connection issues

## Common Issues & Fixes

### Issue 1: MCP Not Responding

**Symptom:** `curl http://localhost:5000/healthz` fails

**Fix:**
```bash
# Check if MCP container is running
docker ps | grep mcp

# If not running, restart
docker compose restart mcp

# Check MCP logs
docker logs mcp
```

### Issue 2: Tavily 403 Error

**Symptom:** "403 Client Error: Forbidden"

**Fix:**
```bash
# Option 1: Get production API key from https://tavily.com
# Update backend/.env:
TAVILY_API_KEY=your_production_key

# Option 2: Disable Tavily in system prompt
# Edit backend/app/services/agent/react_agent.py
# Remove Tavily from system prompt
```

### Issue 3: Backend Can't Connect to MCP

**Symptom:** "Connection refused" or "Cannot reach MCP"

**Fix:**
```bash
# Check MCP_URL in backend/.env
# Should be: MCP_URL=http://mcp:5000

# Verify MCP container name
docker ps | grep mcp

# If different name, update backend/.env
```

### Issue 4: Tavily Module Not Found

**Symptom:** "ModuleNotFoundError: No module named 'tavily'"

**Fix:**
```bash
# Reinstall dependencies
docker compose down
docker compose up --build --no-cache
```

## Step 8: Full System Test

Once tools are working, test the full flow:

1. Go to http://localhost:3000
2. Login
3. Ask: "What's trending?"
4. Check backend logs for:
   - `[INFO] Tool action detected: Google_Trends_MCP`
   - `[INFO] Tool result: ...`
5. Ask: "Search for LangChain"
6. Check backend logs for:
   - `[INFO] Tool action detected: Tavily_Search`
   - `[INFO] Tool result: ...`

## Debugging Checklist

- [ ] Docker Desktop running
- [ ] All containers up (`docker ps`)
- [ ] MCP health check passes
- [ ] Backend health check passes
- [ ] Tavily API key valid
- [ ] Backend logs show no errors
- [ ] Tool test script runs successfully
- [ ] Frontend can reach backend
- [ ] Tool invocation detected in logs
- [ ] Tool results returned to agent

## If Still Failing

1. **Collect logs:**
   ```bash
   docker logs backend > backend.log
   docker logs mcp > mcp.log
   docker logs frontend > frontend.log
   ```

2. **Check network:**
   ```bash
   docker network ls
   docker network inspect google-news-trends-mcp_default
   ```

3. **Restart everything:**
   ```bash
   docker compose down
   docker compose up --build
   ```

4. **Check environment:**
   ```bash
   docker exec backend cat /app/.env | grep -E "TAVILY|MCP"
   ```

## Next Steps

Once you've debugged:
1. Share the error messages you find
2. I'll help fix the specific issue
3. We'll verify both tools work
4. System will be fully functional

**Start with Step 1 and work through each step, noting any errors.**
