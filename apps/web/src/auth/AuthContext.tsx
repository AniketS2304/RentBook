import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import type { OwnerBrief, LoginRequest, RegisterRequest } from '../types/api';
import { apiClient, api } from '../api';
import { ApiClientError } from '../api/errors';
import type { ITokenStorage } from './tokenStorage';
import { defaultWebTokenStorage } from './tokenStorage';

export interface AuthContextType {
  user: OwnerBrief | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
  storage?: ITokenStorage;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({
  children,
  storage = defaultWebTokenStorage,
}) => {
  const [user, setUser] = useState<OwnerBrief | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const logout = useCallback(async () => {
    try {
      await storage.clear();
    } finally {
      setUser(null);
      setError(null);
    }
  }, [storage]);

  useEffect(() => {
    let isMounted = true;

    apiClient.setOnAuthFailure(() => {
      if (isMounted) {
        logout();
      }
    });

    const initAuth = async () => {
      try {
        const refreshToken = await storage.getRefreshToken();
        if (!refreshToken) {
          if (isMounted) setIsLoading(false);
          return;
        }

        const res = await api.auth.refresh({ refresh_token: refreshToken });
        await storage.setAccessToken(res.access_token);
        if (res.refresh_token) {
          await storage.setRefreshToken(res.refresh_token);
        }

        const cachedUser = typeof window !== 'undefined' && window.sessionStorage
          ? window.sessionStorage.getItem('rb_web_user')
          : null;

        if (isMounted && cachedUser) {
          try {
            setUser(JSON.parse(cachedUser));
          } catch {
            // ignore
          }
        }
      } catch {
        if (isMounted) {
          await storage.clear();
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    initAuth();

    return () => {
      isMounted = false;
    };
  }, [storage, logout]);

  const login = useCallback(
    async (credentials: LoginRequest) => {
      setError(null);
      try {
        const response = await api.auth.login(credentials);
        await storage.setAccessToken(response.access_token);
        await storage.setRefreshToken(response.refresh_token);

        if (typeof window !== 'undefined' && window.sessionStorage) {
          window.sessionStorage.setItem('rb_web_user', JSON.stringify(response.user));
        }

        setUser(response.user);
      } catch (err: any) {
        const msg = err instanceof ApiClientError ? err.message : 'Login failed. Please try again.';
        setError(msg);
        throw err;
      }
    },
    [storage]
  );

  const register = useCallback(
    async (data: RegisterRequest) => {
      setError(null);
      try {
        const response = await api.auth.register(data);
        await storage.setAccessToken(response.access_token);
        await storage.setRefreshToken(response.refresh_token);

        const newUser: OwnerBrief = {
          id: response.id,
          email: response.email,
          full_name: response.full_name,
        };

        if (typeof window !== 'undefined' && window.sessionStorage) {
          window.sessionStorage.setItem('rb_web_user', JSON.stringify(newUser));
        }

        setUser(newUser);
      } catch (err: any) {
        const msg = err instanceof ApiClientError ? err.message : 'Registration failed. Please try again.';
        setError(msg);
        throw err;
      }
    },
    [storage]
  );

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      error,
      login,
      register,
      logout,
      clearError,
    }),
    [user, isLoading, error, login, register, logout, clearError]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
