from groq import Groq
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
import asyncio
import re

from app.core.config import settings
from app.services.tools.tavily import tavily_tool
from app.services.tools.google_trends_mcp import google_trends_tool
from app.services.db.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class ReActAgent:
    """ReAct agent using Groq API with tool invocation."""

    def __init__(self):
        """Initialize ReAct agent."""
        self.max_iterations = settings.agent_max_iterations
        self.timeout = settings.agent_timeout
        self.groq_api_key = settings.groq_api_key if hasattr(settings, 'groq_api_key') else None
        self.model_name = "llama-3.3-70b-versatile"
        self.temperature = 0.7

    def _create_system_prompt(self) -> str:
        """Create system prompt for the agent."""
        return """You are a helpful AI assistant with access to tools.

You have access to the following tools:
1. Tavily_Search: Search the web for current information, news, and recent events
2. Google_Trends_MCP: Get trending topics and popular searches

When you need to use a tool, respond with:
ACTION: <tool_name>
INPUT: <tool_input>

Then I will provide the tool result, and you can continue.

If you don't need tools, just provide your answer directly.

Tool names must be exactly: Tavily_Search or Google_Trends_MCP"""

    def _call_groq(self, messages: List[Dict[str, str]]) -> str:
        """Call Groq API (synchronous)."""
        try:
            client = Groq(api_key=self.groq_api_key)
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise

    def _parse_action(self, text: str) -> Optional[Dict[str, str]]:
        """Parse ACTION and INPUT from agent response."""
        # Look for ACTION: tool_name pattern
        action_match = re.search(r'ACTION:\s*(\w+)', text, re.IGNORECASE)
        if not action_match:
            return None
        
        tool_name = action_match.group(1)
        
        # Look for INPUT: ... pattern
        input_match = re.search(r'INPUT:\s*(.+?)(?:\n|$)', text, re.IGNORECASE | re.DOTALL)
        tool_input = input_match.group(1).strip() if input_match else ""
        
        return {
            "tool": tool_name,
            "input": tool_input,
        }

    async def _invoke_tool(self, tool_name: str, tool_input: str) -> str:
        """Invoke a tool and return formatted result."""
        try:
            if tool_name == "Tavily_Search":
                logger.info(f"Invoking Tavily_Search with input: {tool_input}")
                result = await tavily_tool.search(tool_input, max_results=5)
                
                if not result.get("success"):
                    error_msg = result.get("error", "Unknown error")
                    logger.warning(f"Tavily search failed: {error_msg}")
                    # Return a message indicating search failed, agent will use LLM knowledge
                    return f"Web search unavailable (API error: {error_msg}). I'll provide information based on my knowledge."
                
                formatted = tavily_tool.format_results(result)
                return formatted
            
            elif tool_name == "Google_Trends_MCP":
                logger.info(f"Invoking Google_Trends_MCP with input: {tool_input}")
                result = await google_trends_tool.get_trending_terms()
                
                if not result.get("success"):
                    error_msg = result.get("error", "Unknown error")
                    logger.warning(f"Google Trends failed: {error_msg}")
                    return f"Trends service unavailable (API error: {error_msg}). I'll provide information based on my knowledge."
                
                formatted = google_trends_tool.format_trends(result)
                return formatted
            
            else:
                return f"Unknown tool: {tool_name}"
        
        except Exception as e:
            logger.error(f"Tool invocation error: {str(e)}")
            return f"Tool error: {str(e)}. I'll provide information based on my knowledge."

    async def process_message(
        self,
        user_message: str,
        conversation_id: str,
        user_id: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process user message with ReAct loop and stream response.
        
        Args:
            user_message: User's message
            conversation_id: Conversation ID
            user_id: User ID
            
        Yields:
            Dictionary with event type and data
        """
        try:
            # Emit loading event immediately
            yield {
                "event": "loading",
                "data": {"status": "Agent is thinking..."},
            }
            
            # Load conversation history
            messages_data = supabase_client.get_recent_messages(
                conversation_id, user_id, limit=10
            )
            
            # Format history for API
            messages = [{"role": "system", "content": self._create_system_prompt()}]
            
            for msg in messages_data:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            logger.info(f"Processing message for user {user_id}")
            
            # ReAct loop
            iteration = 0
            final_response = None
            
            while iteration < self.max_iterations:
                iteration += 1
                logger.info(f"ReAct iteration {iteration}/{self.max_iterations}")
                
                # Emit responding event
                yield {
                    "event": "responding",
                    "data": {"status": "Generating response..."},
                }
                
                # Call Groq API
                response = await asyncio.wait_for(
                    asyncio.to_thread(self._call_groq, messages),
                    timeout=self.timeout,
                )
                
                logger.info(f"Agent response (iteration {iteration}): {response[:100]}...")
                
                # Check if response contains tool action
                action = self._parse_action(response)
                
                if action:
                    # Tool invocation detected
                    tool_name = action["tool"]
                    tool_input = action["input"]
                    
                    logger.info(f"Tool action detected: {tool_name}")
                    
                    # Emit tool activity event
                    tool_display_name = "Web Search" if tool_name == "Tavily_Search" else "Google Trends"
                    yield {
                        "event": "tool_activity",
                        "data": {
                            "tool": tool_name,
                            "status": "started",
                            "message": f"Using {tool_display_name}..."
                        }
                    }
                    
                    # Invoke tool
                    tool_result = await self._invoke_tool(tool_name, tool_input)
                    
                    logger.info(f"Tool result: {tool_result[:100]}...")
                    
                    # Emit tool completion event
                    yield {
                        "event": "tool_activity",
                        "data": {
                            "tool": tool_name,
                            "status": "completed"
                        }
                    }
                    
                    # Add assistant response and tool result to messages
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": f"Tool result:\n{tool_result}"
                    })
                    
                    # Continue loop for next iteration
                    continue
                
                else:
                    # No tool action, this is the final response
                    final_response = response
                    logger.info(f"Final response generated at iteration {iteration}")
                    break
            
            # If we hit max iterations without final response, use last response
            if final_response is None:
                final_response = response
                logger.warning(f"Max iterations reached, using last response")
            
            # Emit streaming event
            yield {
                "event": "streaming",
                "data": {"status": "Streaming response..."},
            }
            
            # Stream response tokens
            for token in final_response.split():
                yield {
                    "event": "token",
                    "data": {"token": token + " "},
                }
            
            # Save agent response
            supabase_client.save_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=final_response,
            )
            
            # Emit done event
            yield {
                "event": "done",
                "data": {"message_id": "generated"},
            }
            
        except asyncio.TimeoutError:
            logger.error(f"Agent processing timed out after {self.timeout}s")
            yield {
                "event": "error",
                "data": {"error": "Request timed out"},
            }
        except Exception as e:
            logger.error(f"Agent processing error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            yield {
                "event": "error",
                "data": {"error": str(e)},
            }

    async def health_check(self) -> bool:
        """Check if agent dependencies are healthy."""
        try:
            # Check MCP health
            mcp_healthy = await google_trends_tool.health_check()
            if not mcp_healthy:
                logger.warning("MCP service is not healthy")
            
            return mcp_healthy
        except Exception as e:
            logger.error(f"Agent health check failed: {str(e)}")
            return False


# Global instance
react_agent = ReActAgent()
