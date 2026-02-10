from tavily import TavilyClient
from app.core.config import settings
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TavilySearchTool:
    """Wrapper for Tavily web search API."""

    def __init__(self):
        """Initialize Tavily client."""
        self.client = TavilyClient(api_key=settings.tavily_api_key)

    async def search(
        self,
        query: str,
        max_results: int = 5,
        include_answer: bool = True,
    ) -> Dict[str, Any]:
        """
        Search the web using Tavily API.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            include_answer: Whether to include AI-generated answer
            
        Returns:
            Dictionary with search results
        """
        try:
            logger.info(f"Tavily search: {query}")
            
            response = self.client.search(
                query=query,
                max_results=max_results,
                include_answer=include_answer,
            )
            
            logger.info(f"Tavily search completed: {len(response.get('results', []))} results")
            
            return {
                "success": True,
                "query": query,
                "results": response.get("results", []),
                "answer": response.get("answer", ""),
                "raw_response": response,
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Tavily search error: {error_msg}")
            
            return {
                "success": False,
                "query": query,
                "error": error_msg,
                "results": [],
                "answer": "",
            }

    async def search_with_context(
        self,
        query: str,
        context: Optional[str] = None,
        max_results: int = 5,
    ) -> Dict[str, Any]:
        """
        Search with additional context.
        
        Args:
            query: Search query
            context: Additional context for the search
            max_results: Maximum number of results
            
        Returns:
            Dictionary with search results
        """
        if context:
            full_query = f"{query} {context}"
        else:
            full_query = query
        
        return await self.search(full_query, max_results)

    def format_results(self, search_result: Dict[str, Any]) -> str:
        """
        Format search results for agent consumption.
        
        Args:
            search_result: Raw search result from search()
            
        Returns:
            Formatted string for agent
        """
        if not search_result["success"]:
            return f"Search failed: {search_result['error']}"
        
        formatted = f"Search Results for '{search_result['query']}':\n\n"
        
        if search_result["answer"]:
            formatted += f"Answer: {search_result['answer']}\n\n"
        
        if search_result["results"]:
            formatted += "Top Results:\n"
            for i, result in enumerate(search_result["results"], 1):
                formatted += f"\n{i}. {result.get('title', 'No title')}\n"
                formatted += f"   URL: {result.get('url', 'No URL')}\n"
                formatted += f"   {result.get('content', 'No content')}\n"
        else:
            formatted += "No results found."
        
        return formatted


# Global instance
tavily_tool = TavilySearchTool()
