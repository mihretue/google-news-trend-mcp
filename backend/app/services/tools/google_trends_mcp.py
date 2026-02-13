import logging
from typing import Dict, Any
from pytrends.request import TrendReq

logger = logging.getLogger(__name__)


class GoogleTrendsMCPTool:
    """Wrapper for Google Trends data using pytrends."""

    def __init__(self):
        """Initialize Google Trends tool."""
        self.pytrends = TrendReq(hl='en-US', tz=360)

    async def get_trending_terms(self, geo: str = "US") -> Dict[str, Any]:
        """
        Get trending terms from Google Trends.
        
        Args:
            geo: Geographic region (default: US)
            
        Returns:
            Dictionary with trending terms
        """
        try:
            logger.info(f"Fetching trending terms for geo={geo}")
            
            # Get trending searches for the specified region
            trending_searches = self.pytrends.trending_searches(pn=geo)
            
            # Convert to list of dictionaries
            trends = [
                {"keyword": keyword, "rank": idx + 1}
                for idx, keyword in enumerate(trending_searches[0].values)
            ]
            
            logger.info(f"Trending terms fetched successfully: {len(trends)} trends")
            
            return {
                "success": True,
                "geo": geo,
                "trends": trends,
                "raw_response": trending_searches,
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Trends error: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "trends": [],
            }

    async def get_news_by_keyword(self, keyword: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Get news articles by keyword using Google Trends.
        
        Args:
            keyword: Search keyword
            max_results: Maximum number of results
            
        Returns:
            Dictionary with news articles
        """
        try:
            logger.info(f"Fetching news for keyword={keyword}")
            
            # Get related queries for the keyword
            self.pytrends.build_payload([keyword], timeframe='today 1m')
            related_queries = self.pytrends.related_queries()
            
            # Extract top queries
            top_queries = related_queries.get(keyword, {}).get('top', [])
            
            articles = [
                {
                    "title": f"Trending: {query['query']}",
                    "url": f"https://trends.google.com/trends/explore?q={query['query']}",
                    "summary": f"Interest: {query['value']}"
                }
                for query in top_queries[:max_results]
            ]
            
            logger.info(f"News fetched successfully")
            
            return {
                "success": True,
                "keyword": keyword,
                "articles": articles,
                "raw_response": related_queries,
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"News error: {error_msg}")
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
                    rank = trend.get("rank", "N/A")
                    formatted += f"{i}. {keyword} (Rank: {rank})\n"
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
                        formatted += f"   {summary}\n"
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
        Check if tool is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            logger.info("Google Trends tool health check")
            # Try to fetch trending searches to verify connectivity
            self.pytrends.trending_searches(pn='US')
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return False


# Global instance
google_trends_tool = GoogleTrendsMCPTool()
