#!/usr/bin/env python3
"""
Test script to verify ReAct loop implementation.
Tests tool invocation and response generation.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.agent.react_agent import react_agent
from app.services.db.supabase_client import supabase_client
from app.core.config import settings


async def test_react_loop():
    """Test the ReAct loop with various prompts."""
    
    print("=" * 60)
    print("ReAct Loop Test")
    print("=" * 60)
    
    # Test prompts
    test_cases = [
        {
            "name": "Trends Query",
            "prompt": "What's trending on Google right now?",
            "expected_tool": "Google_Trends_MCP",
        },
        {
            "name": "Web Search Query",
            "prompt": "Search the web for information about LangChain agents",
            "expected_tool": "Tavily_Search",
        },
        {
            "name": "General Knowledge",
            "prompt": "What is machine learning?",
            "expected_tool": None,
        },
    ]
    
    for test_case in test_cases:
        print(f"\n{'=' * 60}")
        print(f"Test: {test_case['name']}")
        print(f"Prompt: {test_case['prompt']}")
        print(f"Expected Tool: {test_case['expected_tool'] or 'None (LLM only)'}")
        print("-" * 60)
        
        try:
            # Create a test conversation ID
            test_conversation_id = "test-conv-" + str(hash(test_case['prompt']))[:8]
            test_user_id = "test-user-123"
            
            # Process message
            tool_invoked = None
            response_text = ""
            
            async for event in react_agent.process_message(
                test_case['prompt'],
                test_conversation_id,
                test_user_id,
            ):
                event_type = event.get("event")
                event_data = event.get("data", {})
                
                if event_type == "loading":
                    print(f"[LOADING] {event_data.get('status')}")
                
                elif event_type == "responding":
                    print(f"[RESPONDING] {event_data.get('status')}")
                
                elif event_type == "tool_activity":
                    tool_name = event_data.get("tool")
                    status = event_data.get("status")
                    message = event_data.get("message", "")
                    
                    if status == "started":
                        tool_invoked = tool_name
                        print(f"[TOOL INVOKED] {tool_name}: {message}")
                    elif status == "completed":
                        print(f"[TOOL COMPLETED] {tool_name}")
                
                elif event_type == "streaming":
                    print(f"[STREAMING] {event_data.get('status')}")
                
                elif event_type == "token":
                    token = event_data.get("token", "")
                    response_text += token
                    # Print first 50 chars of response
                    if len(response_text) <= 50:
                        print(f"[TOKEN] {token}", end="", flush=True)
                
                elif event_type == "done":
                    print(f"\n[DONE]")
                
                elif event_type == "error":
                    print(f"[ERROR] {event_data.get('error')}")
            
            # Verify results
            print(f"\nResponse (first 100 chars): {response_text[:100]}...")
            print(f"Tool Invoked: {tool_invoked or 'None'}")
            
            if test_case['expected_tool']:
                if tool_invoked == test_case['expected_tool']:
                    print(f"✅ PASS: Correct tool invoked")
                else:
                    print(f"❌ FAIL: Expected {test_case['expected_tool']}, got {tool_invoked}")
            else:
                if tool_invoked is None:
                    print(f"✅ PASS: No tool invoked (as expected)")
                else:
                    print(f"⚠️  WARNING: Tool invoked when not expected: {tool_invoked}")
        
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 60}")
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_react_loop())
