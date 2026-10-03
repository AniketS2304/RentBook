import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from '../client';
import { InMemoryTokenStorage } from '../../auth/tokenStorage';
import { ApiClientError } from '../errors';

describe('ApiClient (Web)', () => {
  let storage: InMemoryTokenStorage;
  let client: ApiClient;
  let onAuthFailureMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    storage = new InMemoryTokenStorage();
    onAuthFailureMock = vi.fn();
    client = new ApiClient({
      baseUrl: 'http://test-api:8000/api/v1',
      timeoutMs: 1000,
      storage,
      onAuthFailure: onAuthFailureMock,
    });
    vi.restoreAllMocks();
  });

  it('attaches Bearer token when present in storage', async () => {
    storage.setAccessToken('valid-access-token');

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'ok' }),
    });
    global.fetch = mockFetch;

    const res = await client.get('/health');
    expect(res).toEqual({ status: 'ok' });

    expect(mockFetch).toHaveBeenCalledWith(
      'http://test-api:8000/api/v1/health',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer valid-access-token',
        }),
      })
    );
  });

  it('normalizes error responses into ApiClientError', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({
        detail: 'Property not found',
        code: 'PROPERTY_NOT_FOUND',
      }),
    });
    global.fetch = mockFetch;

    await expect(client.get('/properties/123')).rejects.toThrow('Property not found');

    try {
      await client.get('/properties/123');
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiClientError);
      expect(err.status).toBe(404);
      expect(err.code).toBe('PROPERTY_NOT_FOUND');
      expect(err.isNotFound).toBe(true);
    }
  });

  it('handles request timeout cleanly', async () => {
    client = new ApiClient({
      baseUrl: 'http://test-api:8000/api/v1',
      timeoutMs: 50,
      storage,
    });

    global.fetch = vi.fn().mockImplementation((_url, { signal }) => {
      return new Promise((_, reject) => {
        signal.addEventListener('abort', () => {
          const abortError = new Error('The operation was aborted');
          abortError.name = 'AbortError';
          reject(abortError);
        });
      });
    });

    await expect(client.get('/dashboard')).rejects.toThrow(/timed out/);
  });

  it('automatically refreshes token on 401 and retries original request', async () => {
    storage.setAccessToken('expired-access-token');
    storage.setRefreshToken('valid-refresh-token');

    let requestCount = 0;
    const mockFetch = vi.fn().mockImplementation((url: string, options: any) => {
      if (url.includes('/auth/refresh')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            access_token: 'new-fresh-access-token',
            refresh_token: 'new-rotated-refresh-token',
            token_type: 'bearer',
          }),
        });
      }

      if (url.includes('/dashboard')) {
        requestCount++;
        if (requestCount === 1) {
          // First attempt with expired token -> 401
          return Promise.resolve({
            ok: false,
            status: 401,
            json: async () => ({ detail: 'Token expired', code: 'TOKEN_EXPIRED' }),
          });
        }
        // Second attempt with new token -> 200
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            total_expected_paise: 800000,
            authHeaderReceived: options.headers.Authorization,
          }),
        });
      }

      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });
    global.fetch = mockFetch;

    const data: any = await client.get('/dashboard');
    expect(data.total_expected_paise).toBe(800000);
    expect(storage.getAccessToken()).toBe('new-fresh-access-token');
    expect(storage.getRefreshToken()).toBe('new-rotated-refresh-token');
    expect(requestCount).toBe(2);
  });

  it('queues concurrent 401 requests into a single refresh call (mutex queue)', async () => {
    storage.setAccessToken('expired-access-token');
    storage.setRefreshToken('valid-refresh-token');

    let refreshCallCount = 0;
    const mockFetch = vi.fn().mockImplementation(async (url: string, options: any) => {
      if (url.includes('/auth/refresh')) {
        refreshCallCount++;
        // Simulate network delay for refresh
        await new Promise((resolve) => setTimeout(resolve, 30));
        return {
          ok: true,
          status: 200,
          json: async () => ({
            access_token: 'new-shared-access-token',
            refresh_token: 'new-shared-refresh-token',
            token_type: 'bearer',
          }),
        };
      }

      if (url.includes('/endpoint-')) {
        const auth = options?.headers?.Authorization;
        if (auth === 'Bearer expired-access-token') {
          return {
            ok: false,
            status: 401,
            json: async () => ({ detail: 'Token expired', code: 'TOKEN_EXPIRED' }),
          };
        }
        return {
          ok: true,
          status: 200,
          json: async () => ({ success: true, url }),
        };
      }

      return { ok: false, status: 404, json: async () => ({}) };
    });
    global.fetch = mockFetch;

    // Trigger two requests simultaneously
    const [res1, res2] = await Promise.all([
      client.get('/endpoint-1'),
      client.get('/endpoint-2'),
    ]);

    expect(res1).toEqual({ success: true, url: 'http://test-api:8000/api/v1/endpoint-1' });
    expect(res2).toEqual({ success: true, url: 'http://test-api:8000/api/v1/endpoint-2' });
    // Crucial check: only ONE refresh call occurred!
    expect(refreshCallCount).toBe(1);
  });

  it('handles refresh token failure by logging out and rejecting queued requests', async () => {
    storage.setAccessToken('expired-access-token');
    storage.setRefreshToken('invalid-refresh-token');

    const mockFetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/refresh')) {
        return Promise.resolve({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Invalid refresh token', code: 'INVALID_REFRESH_TOKEN' }),
        });
      }
      return Promise.resolve({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Token expired', code: 'TOKEN_EXPIRED' }),
      });
    });
    global.fetch = mockFetch;

    await expect(client.get('/protected-resource')).rejects.toThrow();
    expect(onAuthFailureMock).toHaveBeenCalledTimes(1);
    expect(storage.getAccessToken()).toBeNull();
    expect(storage.getRefreshToken()).toBeNull();
  });

  it('does not retry arbitrary 4xx errors like 400 or 422', async () => {
    let callCount = 0;
    const mockFetch = vi.fn().mockImplementation(() => {
      callCount++;
      return Promise.resolve({
        ok: false,
        status: 422,
        json: async () => ({ detail: 'Validation failed', code: 'VALIDATION_ERROR' }),
      });
    });
    global.fetch = mockFetch;

    await expect(client.post('/properties', {})).rejects.toThrow('Validation failed');
    expect(callCount).toBe(1);
  });
});
