#!/usr/bin/env python3
"""
Direct tool testing - run this to debug tool issues.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.tools.tavily import tavily_tool
from app.services.tools.google_trends_mcp import google_trends_tool
from app.core.config import settings


async def test_tavily():
    """Test Tavily search tool."""
    print("\n" + "=" * 70)
    print("TESTING TAVILY SEARCH")
    print("=" * 70)
    
    print(f"API Key: {settings.tavily_api_key[:20]}...")
    print(f"Query: 'LangChain agents'")
    print("-" * 70)
    
    try:
        result = await tavily_tool.search("LangChain agents", max_results=3)
        
        print(f"Success: {result['success']}")
        
        if result['success']:
            print(f"Results found: {len(result['results'])}")
            if result['answer']:
                print(f"Answer: {result['answer'][:150]}...")
            if result['results']:
                print(f"\nTop result:")
                print(f"  Title: {result['results'][0].get('title', 'N/A')}")
                print(f"  URL: {result['results'][0].get('url', 'N/A')}")
            print("\n✅ TAVILY WORKS")
        else:
            print(f"Error: {result['error']}")
            print("\n❌ TAVILY FAILED")
    
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n❌ TAVILY EXCEPTION")


async def test_mcp():
    """Test Google Trends MCP tool."""
    print("\n" + "=" * 70)
    print("TESTING GOOGLE TRENDS MCP")
    print("=" * 70)
    
    print(f"MCP URL: {settings.mcp_url}")
    print(f"MCP Timeout: {settings.mcp_timeout}s")
    print("-" * 70)
    
    try:
        # First check health
        print("Checking MCP health...")
        health = await google_trends_tool.health_check()
        print(f"Health check: {health}")
        
        if not health:
            print("⚠️  MCP health check failed - service may be down")
        
        # Try to get trends
        print("\nFetching trends...")
        result = await google_trends_tool.get_trending_terms()
        
        print(f"Success: {result['success']}")
        
        if result['success']:
            trends = result['trends']
            print(f"Trends found: {len(trends)}")
            if trends:
                print(f"Top trends:")
                for i, trend in enumerate(trends[:3], 1):
                    if isinstance(trend, dict):
                        print(f"  {i}. {trend.get('keyword', 'N/A')} (Volume: {trend.get('volume', 'N/A')})")
                    else:
                        print(f"  {i}. {trend}")
            print("\n✅ MCP WORKS")
        else:
            print(f"Error: {result['error']}")
            print("\n❌ MCP FAILED")
    
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n❌ MCP EXCEPTION")


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("TOOL DEBUGGING TEST")
    print("=" * 70)
    
    await test_tavily()
    await test_mcp()
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
