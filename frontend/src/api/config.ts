export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  // Auth
  signup: `${API_URL}/auth/signup`,
  login: `${API_URL}/auth/login`,
  logout: `${API_URL}/auth/logout`,

  // Chat
  sendMessage: `${API_URL}/chat/message`,
  getConversations: `${API_URL}/chat/conversations`,
  getMessages: (conversationId: string) =>
    `${API_URL}/chat/conversations/${conversationId}/messages`,

  // Health
  health: `${API_URL}/health`,
};
