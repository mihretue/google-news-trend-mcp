"""Debug test for chat functionality with Groq."""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.agent.react_agent import react_agent
from app.services.db.supabase_client import supabase_client


async def test_chat():
    """Test the chat agent with a simple message."""
    print("=" * 60)
    print("Testing Chat Agent with Groq")
    print("=" * 60)
    
    # Test message with valid UUIDs
    user_message = "Hello! Tell me a short joke."
    conversation_id = "550e8400-e29b-41d4-a716-446655440000"  # Valid UUID
    user_id = "550e8400-e29b-41d4-a716-446655440001"  # Valid UUID
    
    print(f"\nUser Message: {user_message}")
    print(f"Conversation ID: {conversation_id}")
    print(f"User ID: {user_id}")
    print("\n" + "-" * 60)
    print("Agent Response:")
    print("-" * 60)
    
    try:
        # Process message through agent
        async for event in react_agent.process_message(
            user_message=user_message,
            conversation_id=conversation_id,
            user_id=user_id,
        ):
            print(f"Event: {event['event']}")
            if event['event'] == 'token':
                print(f"  Token: {event['data']['token']}", end='', flush=True)
            elif event['event'] == 'error':
                print(f"  Error: {event['data']['error']}")
            elif event['event'] == 'done':
                print(f"\n  Done!")
        
        print("\n" + "=" * 60)
        print("Test completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_chat())
