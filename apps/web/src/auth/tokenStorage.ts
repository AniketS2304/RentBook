/**
 * Token Storage Abstraction
 * 
 * Per Phase 10 guidelines:
 * - Access token remains in memory.
 * - Refresh token storage is pluggable.
 *   Note on Web: The current backend returns refresh_token in JSON body rather than HttpOnly cookies.
 *   Documenting this gap: in the current phase, web uses configurable in-memory/session storage
 *   without violating the frozen backend constraint.
 */

export interface ITokenStorage {
  getAccessToken(): Promise<string | null> | string | null;
  setAccessToken(token: string | null): Promise<void> | void;
  getRefreshToken(): Promise<string | null> | string | null;
  setRefreshToken(token: string | null): Promise<void> | void;
  clear(): Promise<void> | void;
}

export class InMemoryTokenStorage implements ITokenStorage {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  getAccessToken(): string | null {
    return this.accessToken;
  }

  setAccessToken(token: string | null): void {
    this.accessToken = token;
  }

  getRefreshToken(): string | null {
    return this.refreshToken;
  }

  setRefreshToken(token: string | null): void {
    this.refreshToken = token;
  }

  clear(): void {
    this.accessToken = null;
    this.refreshToken = null;
  }
}

/**
 * Session storage implementation for web that persists refresh token across page refreshes
 * in the active browser tab while keeping access token in memory.
 */
export class WebTabTokenStorage implements ITokenStorage {
  private accessToken: string | null = null;
  private readonly REFRESH_KEY = 'rb_web_rt';

  getAccessToken(): string | null {
    return this.accessToken;
  }

  setAccessToken(token: string | null): void {
    this.accessToken = token;
  }

  getRefreshToken(): string | null {
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        return window.sessionStorage.getItem(this.REFRESH_KEY);
      }
    } catch {
      // In environments where sessionStorage is blocked (e.g. sandbox/private browsing)
    }
    return null;
  }

  setRefreshToken(token: string | null): void {
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        if (token) {
          window.sessionStorage.setItem(this.REFRESH_KEY, token);
        } else {
          window.sessionStorage.removeItem(this.REFRESH_KEY);
        }
      }
    } catch {
      // fallback
    }
  }

  clear(): void {
    this.accessToken = null;
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        window.sessionStorage.removeItem(this.REFRESH_KEY);
      }
    } catch {
      // fallback
    }
  }
}

export const defaultWebTokenStorage = new WebTabTokenStorage();
