import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from '../client';
import { InMemoryTokenStorage, ExpoSecureTokenStorage } from '../../auth/tokenStorage';
import { ApiClientError } from '../errors';

describe('ApiClient & Storage (Mobile)', () => {
  let storage: InMemoryTokenStorage;
  let client: ApiClient;
  let onAuthFailureMock = vi.fn();

  beforeEach(() => {
    storage = new InMemoryTokenStorage();
    onAuthFailureMock = vi.fn();
    client = new ApiClient({
      baseUrl: 'http://10.0.2.2:8000/api/v1',
      timeoutMs: 1000,
      storage,
      onAuthFailure: onAuthFailureMock as any,
    });
    vi.restoreAllMocks();
  });

  it('correctly uses the configured Android emulator base URL', () => {
    expect((client as any).baseUrl).toBe('http://10.0.2.2:8000/api/v1');
  });

  it('ExpoSecureTokenStorage falls back gracefully in test/mock environment', async () => {
    const secureStorage = new ExpoSecureTokenStorage();
    await secureStorage.setRefreshToken('test-mobile-refresh-token');
    const token = await secureStorage.getRefreshToken();
    expect(token).toBe('test-mobile-refresh-token');

    await secureStorage.clear();
    const cleared = await secureStorage.getRefreshToken();
    expect(cleared).toBeNull();
  });

  it('attaches Bearer token when present in storage', async () => {
    storage.setAccessToken('mobile-access-token');

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'ok' }),
    });
    global.fetch = mockFetch;

    const res = await client.get('/health');
    expect(res).toEqual({ status: 'ok' });

    expect(mockFetch).toHaveBeenCalledWith(
      'http://10.0.2.2:8000/api/v1/health',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer mobile-access-token',
        }),
      })
    );
  });

  it('normalizes error responses into ApiClientError', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({
        detail: 'Tenant not found',
        code: 'TENANT_NOT_FOUND',
      }),
    });
    global.fetch = mockFetch;

    await expect(client.get('/tenants/123')).rejects.toThrow('Tenant not found');

    try {
      await client.get('/tenants/123');
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiClientError);
      expect(err.status).toBe(404);
      expect(err.code).toBe('TENANT_NOT_FOUND');
      expect(err.isNotFound).toBe(true);
    }
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
          return Promise.resolve({
            ok: false,
            status: 401,
            json: async () => ({ detail: 'Token expired', code: 'TOKEN_EXPIRED' }),
          });
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            total_expected_paise: 1200000,
            authHeaderReceived: options.headers.Authorization,
          }),
        });
      }

      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });
    global.fetch = mockFetch;

    const data: any = await client.get('/dashboard');
    expect(data.total_expected_paise).toBe(1200000);
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
        await new Promise((resolve) => setTimeout(resolve, 30));
        return {
          ok: true,
          status: 200,
          json: async () => ({
            access_token: 'new-mobile-shared-token',
            refresh_token: 'new-mobile-shared-rt',
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

    const [res1, res2] = await Promise.all([
      client.get('/endpoint-1'),
      client.get('/endpoint-2'),
    ]);

    expect(res1).toEqual({ success: true, url: 'http://10.0.2.2:8000/api/v1/endpoint-1' });
    expect(res2).toEqual({ success: true, url: 'http://10.0.2.2:8000/api/v1/endpoint-2' });
    expect(refreshCallCount).toBe(1);
  });

  it('clears storage and triggers onAuthFailure when refresh fails', async () => {
    storage.setAccessToken('expired-access-token');
    storage.setRefreshToken('revoked-refresh-token');

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

    await expect(client.get('/protected-mobile')).rejects.toThrow();
    expect(onAuthFailureMock).toHaveBeenCalledTimes(1);
    expect(storage.getAccessToken()).toBeNull();
    expect(storage.getRefreshToken()).toBeNull();
  });
});
