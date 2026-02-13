import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { chatClient } from '../api/chatClient';
import { Message as MessageComponent } from '../components/Message';
import { logger } from '../utils/logger';
import '../styles/chat.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

const Chat: React.FC = () => {
  const navigate = useNavigate();
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [toolActivity, setToolActivity] = useState<string>('');
  const [selectedTool, setSelectedTool] = useState<string>('');
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check authentication
  useEffect(() => {
    if (!chatClient.isAuthenticated()) {
      navigate('/login');
    }
  }, [navigate]);

  // Load or create conversation
  useEffect(() => {
    const initializeChat = async () => {
      try {
        // Try to get existing conversations
        const data = await chatClient.getConversations();
        if (data.conversations && data.conversations.length > 0) {
          const firstConversation = data.conversations[0];
          setConversationId(firstConversation.id);
          // Load messages
          const messagesData = await chatClient.getMessages(firstConversation.id);
          setMessages(
            messagesData.messages.map((msg: any) => ({
              id: msg.id,
              role: msg.role,
              content: msg.content,
              timestamp: msg.created_at,
            }))
          );
        } else {
          // Create new conversation
          const newConversation = await chatClient.createConversation(
            'New Conversation'
          );
          setConversationId(newConversation.id);
        }
      } catch (err) {
        logger.error('Failed to initialize chat', err);
        setError('Failed to load chat');
      }
    };

    initializeChat();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !conversationId || loading) return;

    const userMessage = input.trim();
    setInput('');
    setError('');
    setLoading(true);

    // Add user message immediately
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    // Create placeholder for assistant message
    const assistantMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      let assistantContent = '';

      await chatClient.sendMessage(
        conversationId,
        userMessage,
        (token: string) => {
          assistantContent += token;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1].content = assistantContent;
            return updated;
          });
        },
        (tool: string, status: string) => {
          logger.info(`[TOOL CALLBACK] Tool: ${tool}, Status: ${status}`);
          if (status === 'started') {
            const toolName = tool === 'Tavily_Search' ? '🔍 Web Search' : 
                           tool === 'Google_Trends_MCP' ? '📈 Google Trends' : 
                           tool;
            logger.info(`[TOOL DISPLAY] Setting tool activity to: ${toolName}`);
            setToolActivity(toolName);
            // Keep tool visible for at least 1 second
            setTimeout(() => {
              setToolActivity('');
            }, 1000);
          } else if (status === 'completed') {
            logger.info(`[TOOL DISPLAY] Tool completed`);
            // Don't clear immediately, let the 1 second timeout handle it
          }
        },
        (error: string) => {
          setError(error);
          setToolActivity('');
          setSelectedTool('');
          setLoadingStatus('');
        },
        (status: string) => {
          setLoadingStatus(status);
        },
        (tool: string, toolName: string) => {
          logger.info(`[TOOL SELECTED] Tool: ${tool}, Display name: ${toolName}`);
          const emoji = tool === 'Tavily_Search' ? '🔍' : '📈';
          setSelectedTool(`${emoji} Selected: ${toolName}`);
        }
      );

      setToolActivity('');
    } catch (err) {
      logger.error('Failed to send message', err);
      setError('Failed to send message');
      // Remove the placeholder assistant message
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
      setSelectedTool('');
    }
  };

  const handleLogout = async () => {
    try {
      await chatClient.logout();
      navigate('/login');
    } catch (err) {
      console.log("error 1 ",err)
      logger.error('Logout failed', err);
      navigate('/login');
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>LangChain ReAct Chatbot</h1>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>Start a conversation by typing a message below</p>
          </div>
        ) : (
          messages.map((message) => (
            <MessageComponent key={message.id} message={message} />
          ))
        )}
        {loadingStatus && <div className="loading-status">⏳ {loadingStatus}</div>}
        {selectedTool && <div className="tool-activity">{selectedTool}</div>}
        {toolActivity && <div className="tool-activity">{toolActivity}</div>}
        <div ref={messagesEndRef} />
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSendMessage} className="chat-input-form">
  <div className="chat-input-wrapper">
    <input
      type="text"
      value={input}
      onChange={(e) => setInput(e.target.value)}
      placeholder="Type your message..."
      disabled={loading || !conversationId}
      className="chat-input"
    />
    <button
      type="submit"
      disabled={loading || !conversationId || !input.trim()}
      className="send-button"
      aria-label="Send message"
    >
      <svg viewBox="0 0 24 24" width="18" height="18">
        <path
          fill="currentColor"
          d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"
        />
      </svg>
    </button>
  </div>
</form>
    </div>
  );
};

export default Chat;
