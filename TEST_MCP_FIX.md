# Testing the MCP Authorization Fix

## Quick Start

### 1. Rebuild Containers
```bash
docker compose down
docker compose up --build
```

Wait for all containers to be healthy (should see 3 containers running):
```bash
docker ps
```

### 2. Test in Browser

1. Open http://localhost:3000
2. Login with your credentials
3. Try these prompts:

#### Test 1: Trending Topics (Uses MCP)
```
What's trending right now?
```

**Expected:**
- Agent detects trends query
- Invokes Google_Trends_MCP
- Shows actual trending topics
- No 403 error

**Example response:**
```
Based on current Google Trends, here are the top trending topics:
1. AI Agents (Volume: 1.2M)
2. LangChain (Volume: 850K)
3. ReAct Pattern (Volume: 620K)
...
```

#### Test 2: Web Search (Uses Tavily)
```
Search for LangChain
```

**Expected:**
- Agent detects search query
- Tries to invoke Tavily_Search
- Gets 403 error (dev key limitation)
- Falls back to LLM knowledge gracefully
- Returns helpful response

**Example response:**
```
Web search unavailable (API error: 403 Client Error). I'll provide information based on my knowledge.

LangChain is a framework that allows developers to build applications using large language models...
```

#### Test 3: General Knowledge (No Tools)
```
What is machine learning?
```

**Expected:**
- Agent detects general knowledge question
- No tool invocation needed
- Responds directly from LLM

### 3. Check Backend Logs

```bash
# See tool invocation logs
docker logs backend | grep "Tool action"

# See MCP calls
docker logs backend | grep "Fetching trending"

# See all activity
docker logs backend -f
```

### 4. Verify Authorization

Look for these log messages:

```
INFO: Fetching trending terms for geo=US
INFO: Trending terms fetched successfully
```

If you see 403 errors, check:
- MCP container is running: `docker ps | grep mcp`
- MCP logs: `docker logs mcp`
- Backend has SUPABASE_JWT_SECRET: `docker exec backend env | grep JWT`

## Troubleshooting

### Issue: Still getting 403 errors

**Check 1: MCP container running?**
```bash
docker ps | grep mcp
```
Should show mcp container running on port 5000

**Check 2: Backend can reach MCP?**
```bash
docker exec backend curl -X GET http://mcp:5000/health
```
Should return 200 (or 401 if auth is working)

**Check 3: JWT secret configured?**
```bash
docker exec backend env | grep SUPABASE_JWT_SECRET
```
Should show the secret value

**Check 4: Backend logs**
```bash
docker logs backend --tail 50
```
Look for error messages about token creation or MCP calls

### Issue: MCP container won't start

```bash
docker logs mcp
```

Common issues:
- Missing `python-jose` dependency (should be fixed in pyproject.toml)
- Port 5000 already in use
- Network issues

### Issue: Tavily still returns 403

This is expected with dev API key. To fix:
1. Get production key from https://tavily.com
2. Update `backend/.env`: `TAVILY_API_KEY=your_key`
3. Restart: `docker compose restart backend`

## Success Indicators

✅ **System is working if:**
- Trending queries return actual trending data
- Web search queries gracefully fall back to LLM knowledge
- General knowledge questions work
- No crashes or 500 errors
- Backend logs show "Tool action detected" messages

✅ **MCP is working if:**
- Backend logs show "Fetching trending terms"
- Backend logs show "Trending terms fetched successfully"
- No 403 errors in backend logs

## Next Steps

1. Test all three prompt types above
2. Check backend logs for any errors
3. If everything works, system is ready for deployment
4. Optional: Get Tavily production key for full web search

## Questions?

Check these files for more info:
- `MCP_AUTHORIZATION_FIX.md` - Technical details of the fix
- `CURRENT_STATUS.md` - Overall system status
- `REACT_LOOP_IMPLEMENTATION.md` - How ReAct loop works
