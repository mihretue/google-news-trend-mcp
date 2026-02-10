import axios, { AxiosInstance, AxiosError } from 'axios';
import { API_URL, API_ENDPOINTS } from './config';
import { logger } from '../utils/logger';

class ChatClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for token injection
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          logger.warn('Token expired or invalid');
          this.clearToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  private setToken(token: string): void {
    localStorage.setItem('auth_token', token);
  }

  private clearToken(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_id');
  }

  async signup(email: string, password: string): Promise<any> {
    try {
      const response = await this.client.post(API_ENDPOINTS.signup, {
        email,
        password,
      });
      this.setToken(response.data.access_token);
      return response.data;
    } catch (error) {
      logger.error('Signup failed', error);
      throw error;
    }
  }

  async login(email: string, password: string): Promise<any> {
    try {
      const response = await this.client.post(API_ENDPOINTS.login, {
        email,
        password,
      });
      this.setToken(response.data.access_token);
      return response.data;
    } catch (error) {
      logger.error('Login failed', error);
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      await this.client.post(API_ENDPOINTS.logout);
      this.clearToken();
    } catch (error) {
      logger.error('Logout failed', error);
      this.clearToken();
    }
  }

  async createConversation(title: string): Promise<any> {
    try {
      const response = await this.client.post(
        API_ENDPOINTS.getConversations,
        { title }
      );
      return response.data;
    } catch (error) {
      logger.error('Failed to create conversation', error);
      throw error;
    }
  }

  async getConversations(): Promise<any> {
    try {
      const response = await this.client.get(API_ENDPOINTS.getConversations);
      return response.data;
    } catch (error) {
      logger.error('Failed to get conversations', error);
      throw error;
    }
  }

  async getMessages(conversationId: string): Promise<any> {
    try {
      const response = await this.client.get(
        API_ENDPOINTS.getMessages(conversationId)
      );
      return response.data;
    } catch (error) {
      logger.error('Failed to get messages', error);
      throw error;
    }
  }

  async sendMessage(
    conversationId: string,
    content: string,
    onToken: (token: string) => void,
    onToolActivity: (tool: string, status: string) => void,
    onError: (error: string) => void
  ): Promise<void> {
    try {
      const eventSource = new EventSource(
        `${API_URL}/chat/message?conversation_id=${conversationId}&content=${encodeURIComponent(content)}`,
        {
          withCredentials: true,
        }
      );

      // Inject token manually since EventSource doesn't support headers
      const token = this.getToken();
      if (token) {
        // Create a custom fetch-based SSE connection instead
        this.sendMessageWithFetch(
          conversationId,
          content,
          onToken,
          onToolActivity,
          onError
        );
        return;
      }

      eventSource.addEventListener('token', (event: any) => {
        const data = JSON.parse(event.data);
        onToken(data.token);
      });

      eventSource.addEventListener('tool_activity', (event: any) => {
        const data = JSON.parse(event.data);
        onToolActivity(data.tool, data.status);
      });

      eventSource.addEventListener('error', (event: any) => {
        const data = JSON.parse(event.data);
        onError(data.error);
        eventSource.close();
      });

      eventSource.addEventListener('done', () => {
        eventSource.close();
      });
    } catch (error) {
      logger.error('Failed to send message', error);
      onError('Failed to send message');
    }
  }

  private async sendMessageWithFetch(
    conversationId: string,
    content: string,
    onToken: (token: string) => void,
    onToolActivity: (tool: string, status: string) => void,
    onError: (error: string) => void
  ): Promise<void> {
    try {
      const token = this.getToken();
      const response = await fetch(API_ENDPOINTS.sendMessage, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          content,
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          this.clearToken();
          window.location.href = '/login';
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            const eventType = line.substring(6).trim();
            const dataLine = lines.shift();

            if (dataLine?.startsWith('data:')) {
              const dataStr = dataLine.substring(5).trim();
              const data = JSON.parse(dataStr);

              if (eventType === 'token') {
                onToken(data.token);
              } else if (eventType === 'tool_activity') {
                onToolActivity(data.tool, data.status);
              } else if (eventType === 'error') {
                onError(data.error);
              }
            }
          }
        }
      }
    } catch (error) {
      logger.error('SSE connection error', error);
      onError('Connection error');
    }
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  getUserId(): string | null {
    return localStorage.getItem('user_id');
  }
}

export const chatClient = new ChatClient();
