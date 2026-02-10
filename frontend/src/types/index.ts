// User types
export interface User {
  id: string;
  email: string;
  created_at: string;
}

// Conversation types
export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

// Message types
export interface Message {
  id: string;
  conversation_id: string;
  user_id: string;
  role: 'user' | 'assistant';
  content: string;
  tool_calls?: Record<string, unknown>;
  created_at: string;
}

// API Response types
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ChatMessageRequest {
  conversation_id: string;
  content: string;
}

// SSE Event types
export interface TokenEvent {
  token: string;
}

export interface ToolActivityEvent {
  tool: string;
  status: 'started' | 'completed' | 'failed';
}

export interface DoneEvent {
  message_id: string;
}
