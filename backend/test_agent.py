#!/usr/bin/env python3

print("Testing ReAct agent import...")

try:
    from app.core.config import settings
    print("✅ Settings imported")
except Exception as e:
    print(f"❌ Settings failed: {e}")
    exit(1)

try:
    from app.services.tools.tavily import tavily_tool
    print("✅ Tavily tool imported")
except Exception as e:
    print(f"❌ Tavily tool failed: {e}")
    exit(1)

try:
    from app.services.tools.google_trends_mcp import google_trends_tool
    print("✅ Google Trends tool imported")
except Exception as e:
    print(f"❌ Google Trends tool failed: {e}")
    exit(1)

try:
    from app.services.agent.react_agent import react_agent
    print("✅ ReAct agent imported")
except Exception as e:
    print(f"❌ ReAct agent failed: {e}")
    exit(1)

print("All imports successful!")