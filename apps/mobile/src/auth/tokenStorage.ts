import * as SecureStore from 'expo-secure-store';

/**
 * Token Storage Abstraction for Mobile
 * 
 * - Access token is kept strictly in memory.
 * - Long-lived refresh token is securely stored via expo-secure-store.
 * - In environments where SecureStore native module is unavailable (e.g. Node tests),
 *   gracefully falls back to in-memory storage.
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

export class ExpoSecureTokenStorage implements ITokenStorage {
  private accessToken: string | null = null;
  private readonly REFRESH_KEY = 'rb_mobile_rt';
  private inMemoryFallback = new InMemoryTokenStorage();

  getAccessToken(): string | null {
    return this.accessToken;
  }

  setAccessToken(token: string | null): void {
    this.accessToken = token;
  }

  async getRefreshToken(): Promise<string | null> {
    try {
      if (SecureStore && typeof SecureStore.getItemAsync === 'function') {
        return await SecureStore.getItemAsync(this.REFRESH_KEY);
      }
    } catch {
      // fallback
    }
    return this.inMemoryFallback.getRefreshToken();
  }

  async setRefreshToken(token: string | null): Promise<void> {
    try {
      if (SecureStore && typeof SecureStore.setItemAsync === 'function') {
        if (token) {
          await SecureStore.setItemAsync(this.REFRESH_KEY, token, {
            keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK,
          });
        } else {
          await SecureStore.deleteItemAsync(this.REFRESH_KEY);
        }
        return;
      }
    } catch {
      // fallback
    }
    this.inMemoryFallback.setRefreshToken(token);
  }

  async clear(): Promise<void> {
    this.accessToken = null;
    try {
      if (SecureStore && typeof SecureStore.deleteItemAsync === 'function') {
        await SecureStore.deleteItemAsync(this.REFRESH_KEY);
      }
    } catch {
      // fallback
    }
    this.inMemoryFallback.clear();
  }
}

export const defaultMobileTokenStorage = new ExpoSecureTokenStorage();
