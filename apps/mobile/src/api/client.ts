import { ApiClientError, parseApiError } from './errors';
import type { ITokenStorage } from '../auth/tokenStorage';
import { defaultMobileTokenStorage } from '../auth/tokenStorage';
import { ENV } from '../config/env';
import type { RefreshResponse } from '../types/api';

export interface RequestOptions extends RequestInit {
  params?: Record<string, any>;
  timeoutMs?: number;
  skipAuth?: boolean;
  _retry?: boolean;
}

export interface ApiClientConfig {
  baseUrl?: string;
  timeoutMs?: number;
  storage?: ITokenStorage;
  onAuthFailure?: () => void;
}

export class ApiClient {
  private baseUrl: string;
  private defaultTimeoutMs: number;
  private storage: ITokenStorage;
  private onAuthFailure?: () => void;

  // Refresh token mutex state
  private isRefreshing = false;
  private refreshSubscribers: Array<(token: string) => void> = [];
  private refreshRejectSubscribers: Array<(err: any) => void> = [];

  constructor(config: ApiClientConfig = {}) {
    this.baseUrl = (config.baseUrl || ENV.API_BASE_URL).replace(/\/$/, '');
    this.defaultTimeoutMs = config.timeoutMs || 15000;
    this.storage = config.storage || defaultMobileTokenStorage;
    this.onAuthFailure = config.onAuthFailure;
  }

  public setOnAuthFailure(callback: () => void): void {
    this.onAuthFailure = callback;
  }

  public getStorage(): ITokenStorage {
    return this.storage;
  }

  private onRefreshed(newToken: string): void {
    this.refreshSubscribers.forEach((callback) => callback(newToken));
    this.refreshSubscribers = [];
    this.refreshRejectSubscribers = [];
  }

  private onRefreshFailed(err: any): void {
    this.refreshRejectSubscribers.forEach((callback) => callback(err));
    this.refreshSubscribers = [];
    this.refreshRejectSubscribers = [];
  }

  public async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const {
      params,
      timeoutMs = this.defaultTimeoutMs,
      skipAuth = false,
      _retry = false,
      headers: customHeaders = {},
      ...customOptions
    } = options;

    let url = `${this.baseUrl}/${endpoint.replace(/^\//, '')}`;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          searchParams.append(key, String(val));
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += (url.includes('?') ? '&' : '?') + queryString;
      }
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(customHeaders as Record<string, string>),
    };

    if (!skipAuth) {
      const accessToken = await this.storage.getAccessToken();
      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    let response: Response;
    try {
      response = await fetch(url, {
        ...customOptions,
        headers,
        signal: controller.signal,
      });
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new ApiClientError({
          message: `Request timed out after ${timeoutMs}ms`,
          isTimeout: true,
        });
      }
      throw new ApiClientError({
        message: err.message || 'Network connection failed. Please check your internet.',
        isNetworkError: true,
      });
    } finally {
      clearTimeout(timeoutId);
    }

    if (response.status === 401) {
      const isAuthEndpoint =
        endpoint.includes('/auth/login') ||
        endpoint.includes('/auth/register') ||
        endpoint.includes('/auth/refresh');

      if (_retry || isAuthEndpoint || skipAuth) {
        throw await parseApiError(response);
      }

      if (this.isRefreshing) {
        return new Promise<T>((resolve, reject) => {
          this.refreshSubscribers.push((newToken: string) => {
            const retryHeaders = {
              ...headers,
              Authorization: `Bearer ${newToken}`,
            };
            this.request<T>(endpoint, {
              ...options,
              _retry: true,
              headers: retryHeaders,
            })
              .then(resolve)
              .catch(reject);
          });

          this.refreshRejectSubscribers.push((refreshErr: any) => {
            reject(refreshErr);
          });
        });
      }

      this.isRefreshing = true;
      try {
        const storedRefreshToken = await this.storage.getRefreshToken();
        if (!storedRefreshToken) {
          throw new ApiClientError({
            message: 'Session expired. Please log in again.',
            status: 401,
            code: 'SESSION_EXPIRED',
          });
        }

        const refreshUrl = `${this.baseUrl}/auth/refresh`;
        const refreshResponse = await fetch(refreshUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify({ refresh_token: storedRefreshToken }),
        });

        if (!refreshResponse.ok) {
          throw await parseApiError(refreshResponse);
        }

        const refreshData: RefreshResponse = await refreshResponse.json();
        await this.storage.setAccessToken(refreshData.access_token);
        if (refreshData.refresh_token) {
          await this.storage.setRefreshToken(refreshData.refresh_token);
        }

        this.onRefreshed(refreshData.access_token);

        return await this.request<T>(endpoint, {
          ...options,
          _retry: true,
        });
      } catch (refreshErr) {
        await this.storage.clear();
        this.onRefreshFailed(refreshErr);
        if (this.onAuthFailure) {
          this.onAuthFailure();
        }
        throw refreshErr;
      } finally {
        this.isRefreshing = false;
      }
    }

    if (!response.ok) {
      throw await parseApiError(response);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  }

  public get<T>(endpoint: string, params?: Record<string, any>, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET', params });
  }

  public post<T>(endpoint: string, body?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  public put<T>(endpoint: string, body?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  public delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

export const apiClient = new ApiClient();
