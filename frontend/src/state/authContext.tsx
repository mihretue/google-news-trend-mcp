import React, { createContext, useContext, useState, useEffect } from 'react';
import { chatClient } from '../api/chatClient';
import { logger } from '../utils/logger';

interface AuthContextType {
  isAuthenticated: boolean;
  userId: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('auth_token');
      const uid = localStorage.getItem('user_id');

      if (token && uid) {
        setIsAuthenticated(true);
        setUserId(uid);
      } else {
        setIsAuthenticated(false);
        setUserId(null);
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const data = await chatClient.login(email, password);
      setIsAuthenticated(true);
      setUserId(data.user_id);
      logger.info('User logged in');
    } catch (error) {
      logger.error('Login failed', error);
      throw error;
    }
  };

  const signup = async (email: string, password: string) => {
    try {
      const data = await chatClient.signup(email, password);
      setIsAuthenticated(true);
      setUserId(data.user_id);
      logger.info('User signed up');
    } catch (error) {
      logger.error('Signup failed', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await chatClient.logout();
      setIsAuthenticated(false);
      setUserId(null);
      logger.info('User logged out');
    } catch (error) {
      logger.error('Logout failed', error);
      setIsAuthenticated(false);
      setUserId(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        userId,
        loading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
