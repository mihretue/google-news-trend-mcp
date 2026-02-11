# Tool Debug Checklist

## Quick Start

### 1. Start Docker Desktop
- Open Docker Desktop application
- Wait for it to fully start (green indicator)

### 2. Start Containers
```bash
cd your_project_directory
docker compose down
docker compose up --build
```

Wait 30 seconds for everything to start.

### 3. Verify Containers Running
```bash
docker ps
```

You should see:
- ✅ backend (port 8000)
- ✅ frontend (port 3000)  
- ✅ mcp (port 5000)

If any missing, check logs:
```bash
docker logs backend
docker logs mcp
docker logs frontend
```

---

## Debug Tavily Tool

### Check 1: API Key Valid
```bash
docker exec backend cat /app/.env | grep TAVILY
```

Should show: `TAVILY_API_KEY=tvly-dev-...` or `TAVILY_API_KEY=tvly-...`

### Check 2: Test Tavily Directly
```bash
cd backend
python test_tools_direct.py
```

Look for:
- ✅ "TAVILY WORKS" → Tool is fine
- ❌ "TAVILY FAILED" → API key issue
- ❌ "TAVILY EXCEPTION" → Connection issue

### Check 3: Backend Logs
```bash
docker logs backend | grep -i tavily
```

Look for:
- `Tavily search:` → Tool being called
- `Tavily search error:` → Error message
- `403 Forbidden` → API key issue

### Fix Tavily Issues

**If 403 Forbidden:**
```bash
# Get free production key from https://tavily.com
# Update backend/.env:
TAVILY_API_KEY=your_production_key_here

# Restart backend
docker compose restart backend
```

**If "Connection refused":**
```bash
# Check internet connection
# Check Tavily API status
# Restart backend
docker compose restart backend
```

---

## Debug MCP Tool

### Check 1: MCP Container Running
```bash
docker ps | grep mcp
```

Should show MCP container running on port 5000.

### Check 2: MCP Health Check
```bash
curl http://localhost:5000/healthz
```

Expected: `200 OK` or similar

If fails:
```bash
# Check MCP logs
docker logs mcp

# Restart MCP
docker compose restart mcp
```

### Check 3: Test MCP Directly
```bash
cd backend
python test_tools_direct.py
```

Look for:
- ✅ "MCP WORKS" → Tool is fine
- ❌ "MCP FAILED" → Connection issue
- ❌ "MCP EXCEPTION" → Service error

### Check 4: Backend Logs
```bash
docker logs backend | grep -i "mcp\|trend"
```

Look for:
- `Fetching trending terms` → Tool being called
- `MCP error:` → Error message
- `Connection refused` → MCP not running

### Fix MCP Issues

**If "Connection refused":**
```bash
# Check MCP_URL in backend/.env
# Should be: MCP_URL=http://mcp:5000

# Restart MCP
docker compose restart mcp

# Check MCP logs
docker logs mcp
```

**If MCP not responding:**
```bash
# Restart entire stack
docker compose down
docker compose up --build

# Wait 30 seconds
# Test again
```

---

## Full System Test

Once both tools pass individual tests:

### 1. Test in Browser
- Go to http://localhost:3000
- Login
- Ask: "What's trending?"
- Check for tool activity indicator

### 2. Check Backend Logs
```bash
docker logs backend -f
```

Look for:
- `[INFO] Tool action detected: Google_Trends_MCP`
- `[INFO] Tool result: ...`

### 3. Test Web Search
- Ask: "Search for LangChain"
- Check for tool activity indicator

### 4. Check Backend Logs Again
```bash
docker logs backend -f
```

Look for:
- `[INFO] Tool action detected: Tavily_Search`
- `[INFO] Tool result: ...`

---

## Troubleshooting Matrix

| Symptom | Cause | Fix |
|---------|-------|-----|
| Tavily 403 | Dev API key | Get production key |
| Tavily timeout | Network issue | Check internet |
| MCP not found | Container not running | `docker compose restart mcp` |
| MCP timeout | Service slow | Restart stack |
| No tool invocation | Agent not detecting | Check backend logs |
| Tool invoked but no result | Tool error | Check tool logs |

---

## Commands Reference

```bash
# Start everything
docker compose up --build

# Stop everything
docker compose down

# View logs
docker logs backend -f
docker logs mcp -f
docker logs frontend -f

# Restart specific service
docker compose restart backend
docker compose restart mcp
docker compose restart frontend

# Run test
cd backend
python test_tools_direct.py

# Check environment
docker exec backend cat /app/.env

# Check health
curl http://localhost:8000/health
curl http://localhost:5000/healthz
```

---

## Success Indicators

✅ **Tavily Working:**
- `python test_tools_direct.py` shows "TAVILY WORKS"
- Backend logs show "Tavily search completed"
- Web search prompts trigger tool invocation

✅ **MCP Working:**
- `python test_tools_direct.py` shows "MCP WORKS"
- Backend logs show "Fetching trending terms"
- Trends prompts trigger tool invocation

✅ **System Working:**
- Both tools pass individual tests
- Tool activity indicators show in UI
- Backend logs show tool invocation
- Responses include tool-based information

---

## Next Steps

1. **Run checklist items in order**
2. **Note any errors you find**
3. **Share error messages**
4. **I'll help fix specific issues**

**Start with: `docker ps` to verify containers are running**
