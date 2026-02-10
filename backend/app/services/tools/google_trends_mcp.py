import httpx
from app.core.config import settings
import logging
from typing import Dict, Any, Optional
import asyncio
import json

logger = logging.getLogger(__name__)


class GoogleTrendsMCPTool:
    """Wrapper for Google News Trends MCP server."""

    def __init__(self):
        """Initialize MCP client."""
        self.mcp_url = settings.mcp_url
        self.timeout = settings.mcp_timeout

    async def get_trending_terms(self, geo: str = "US") -> Dict[str, Any]:
        """
        Get trending terms from Google Trends MCP.
        
        Args:
            geo: Geographic region (default: US)
            
        Returns:
            Dictionary with trending terms
        """
        try:
            logger.info(f"Fetching trending terms for geo={geo}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Call MCP tool via HTTP
                endpoint = f"{self.mcp_url}/mcp/tools/call"
                payload = {
                    "name": "get_trending_terms",
                    "arguments": {
                        "geo": geo,
                        "full_data": False,
                    }
                }
                
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Trending terms fetched successfully")
                
                return {
                    "success": True,
                    "geo": geo,
                    "trends": data.get("content", []) if isinstance(data, dict) else data,
                    "raw_response": data,
                }
        except asyncio.TimeoutError:
            error_msg = f"MCP request timed out after {self.timeout}s"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "trends": [],
            }
        except httpx.HTTPError as e:
            error_msg = f"MCP HTTP error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "trends": [],
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"MCP error: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "trends": [],
            }

    async def get_news_by_keyword(self, keyword: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Get news articles by keyword from Google News MCP.
        
        Args:
            keyword: Search keyword
            max_results: Maximum number of results
            
        Returns:
            Dictionary with news articles
        """
        try:
            logger.info(f"Fetching news for keyword={keyword}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                endpoint = f"{self.mcp_url}/mcp/tools/call"
                payload = {
                    "name": "get_news_by_keyword",
                    "arguments": {
                        "keyword": keyword,
                        "max_results": max_results,
                        "full_data": False,
                        "summarize": True,
                    }
                }
                
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"News fetched successfully")
                
                return {
                    "success": True,
                    "keyword": keyword,
                    "articles": data.get("content", []) if isinstance(data, dict) else data,
                    "raw_response": data,
                }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"MCP error: {error_msg}")
            return {
                "success": False,
                "keyword": keyword,
                "error": error_msg,
                "articles": [],
            }

    def format_trends(self, trends_result: Dict[str, Any]) -> str:
        """
        Format trending terms for agent consumption.
        
        Args:
            trends_result: Raw trends result
            
        Returns:
            Formatted string for agent
        """
        if not trends_result["success"]:
            return f"Trends fetch failed: {trends_result['error']}"
        
        formatted = f"Google Trends ({trends_result['geo']}):\n\n"
        
        if trends_result["trends"]:
            for i, trend in enumerate(trends_result["trends"][:10], 1):
                if isinstance(trend, dict):
                    keyword = trend.get("keyword", "No keyword")
                    volume = trend.get("volume", "N/A")
                    formatted += f"{i}. {keyword} (Volume: {volume})\n"
                else:
                    formatted += f"{i}. {trend}\n"
        else:
            formatted += "No trends data available."
        
        return formatted

    def format_news(self, news_result: Dict[str, Any]) -> str:
        """
        Format news articles for agent consumption.
        
        Args:
            news_result: Raw news result
            
        Returns:
            Formatted string for agent
        """
        if not news_result["success"]:
            return f"News fetch failed: {news_result['error']}"
        
        formatted = f"News Articles for '{news_result['keyword']}':\n\n"
        
        if news_result["articles"]:
            for i, article in enumerate(news_result["articles"][:5], 1):
                if isinstance(article, dict):
                    title = article.get("title", "No title")
                    url = article.get("url", "")
                    summary = article.get("summary", "")
                    formatted += f"{i}. {title}\n"
                    if summary:
                        formatted += f"   Summary: {summary[:200]}...\n"
                    if url:
                        formatted += f"   URL: {url}\n"
                    formatted += "\n"
                else:
                    formatted += f"{i}. {article}\n"
        else:
            formatted += "No articles found."
        
        return formatted

    async def health_check(self) -> bool:
        """
        Check if MCP service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.mcp_url}/healthz")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"MCP health check failed: {str(e)}")
            return False


# Global instance
google_trends_tool = GoogleTrendsMCPTool()
