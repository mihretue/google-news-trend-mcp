# Google News Trends MCP Integration Guide

## Overview

The system integrates with the existing `google-news-trends-mcp` folder which provides a complete MCP (Model Context Protocol) server for accessing Google News and Google Trends data.

## MCP Server Location

```
google-news-trends-mcp/
├── main.py                 # FastAPI entry point
├── mcp_server.py          # MCP server configuration
├── tools.py               # Tool implementations
├── auth.py                # Authentication
├── load_var.py            # Environment loading
├── pyproject.toml         # Python dependencies
├── Dockerfile             # Container configuration
├── README.md              # Documentation
└── security/              # Security utilities
    ├── utils.py
    ├── verification.py
    └── __init__.py
```

## Available Tools

The MCP server provides 5 main tools:

### 1. get_trending_terms
Get trending search terms from Google Trends.

**Parameters:**
- `geo` (str): Country code (e.g., 'US', 'GB', 'IN')
- `full_data` (bool): Return full data or summary

**Returns:**
- List of trending keywords with search volume

### 2. get_news_by_keyword
Search for news articles by keyword.

**Parameters:**
- `keyword` (str): Search term
- `period` (int): Days to look back (default: 7)
- `max_results` (int): Maximum results (default: 10)
- `full_data` (bool): Return full article data
- `summarize` (bool): Generate summaries

**Returns:**
- List of news articles with titles, URLs, and summaries

### 3. get_news_by_location
Search for news articles by geographic location.

**Parameters:**
- `location` (str): City/state/country name
- `period` (int): Days to look back
- `max_results` (int): Maximum results
- `full_data` (bool): Return full data
- `summarize` (bool): Generate summaries

**Returns:**
- List of location-specific news articles

### 4. get_news_by_topic
Search for news articles by topic.

**Parameters:**
- `topic` (str): Topic name (WORLD, BUSINESS, TECHNOLOGY, etc.)
- `period` (int): Days to look back
- `max_results` (int): Maximum results
- `full_data` (bool): Return full data
- `summarize` (bool): Generate summaries

**Returns:**
- List of topic-specific news articles

### 5. get_top_news
Get top news stories.

**Parameters:**
- `period` (int): Days to look back (default: 3)
- `max_results` (int): Maximum results (default: 10)
- `full_data` (bool): Return full data
- `summarize` (bool): Generate summaries

**Returns:**
- List of top news articles

## API Endpoints

### Health Check
```
GET /healthz
```
Returns: `ok` (200 status)

### MCP Protocol
```
POST /mcp/tools/call
```
Call MCP tools with JSON payload:
```json
{
  "name": "tool_name",
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

## Docker Integration

### Build the MCP Image
```bash
cd google-news-trends-mcp
docker build -t google-news-trends-mcp:latest .
```

### Run Standalone
```bash
docker run -p 5000:5000 google-news-trends-mcp:latest
```

### Docker Compose Integration
The `docker-compose.yml` includes the MCP service:

```yaml
mcp:
  image: google-news-trends-mcp:latest
  ports:
    - "5000:5000"
  networks:
    - chatbot-network
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5000/healthz"]
    interval: 10s
    timeout: 5s
    retries: 3
```

## Backend Integration

### Configuration
The backend connects to the MCP server via environment variables:

```env
MCP_URL=http://mcp:5000
MCP_TIMEOUT=10
```

### Tool Wrapper
Located at: `backend/app/services/tools/google_trends_mcp.py`

**Methods:**
- `get_trending_terms(geo='US')` - Get trending terms
- `get_news_by_keyword(keyword, max_results=5)` - Search news by keyword
- `format_trends(result)` - Format trends for agent
- `format_news(result)` - Format news for agent
- `health_check()` - Check MCP service health

### ReAct Agent Integration
The ReAct agent uses the MCP tool for:
- Responding to queries about trending topics
- Providing current news information
- Tool selection based on query intent

## Usage Examples

### Get Trending Terms
```python
from backend.app.services.tools.google_trends_mcp import google_trends_tool

result = await google_trends_tool.get_trending_terms(geo="US")
formatted = google_trends_tool.format_trends(result)
print(formatted)
```

### Get News by Keyword
```python
result = await google_trends_tool.get_news_by_keyword("AI", max_results=5)
formatted = google_trends_tool.format_news(result)
print(formatted)
```

### Check Health
```python
is_healthy = await google_trends_tool.health_check()
print(f"MCP Service: {'Healthy' if is_healthy else 'Unhealthy'}")
```

## Error Handling

The tool wrapper handles:
- **Timeout errors**: Returns friendly error message
- **HTTP errors**: Logs and returns error response
- **Connection errors**: Gracefully handles unavailable service
- **Parsing errors**: Returns structured error response

## Performance Considerations

1. **Caching**: Consider caching trending terms (they don't change frequently)
2. **Rate Limiting**: The MCP server may have rate limits
3. **Timeouts**: Default timeout is 10 seconds (configurable)
4. **Batch Requests**: Limit concurrent requests to avoid overload

## Security

The MCP server includes:
- JWT authentication (if configured)
- Authorization middleware
- Request validation
- Error handling without exposing internals

## Troubleshooting

### MCP Service Not Responding
```bash
# Check if service is running
curl http://localhost:5000/healthz

# Check logs
docker logs <container_id>
```

### Connection Timeout
- Increase `MCP_TIMEOUT` in environment
- Check network connectivity
- Verify service is healthy

### Tool Failures
- Check MCP logs for detailed errors
- Verify parameters are correct
- Check internet connectivity for news/trends data

## Future Enhancements

1. **Caching Layer**: Cache trending terms and popular news
2. **Rate Limiting**: Implement rate limiting for API calls
3. **Fallback Strategies**: Use cached data if service is unavailable
4. **Tool Metadata**: Store tool call metadata for analytics
5. **Custom Filters**: Add filtering for news by source, language, etc.

## References

- MCP Server: `google-news-trends-mcp/README.md`
- Backend Integration: `backend/app/services/tools/google_trends_mcp.py`
- ReAct Agent: `backend/app/services/agent/react_agent.py`
- Docker Compose: `docker-compose.yml`
