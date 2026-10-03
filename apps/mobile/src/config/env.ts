import { Platform } from 'react-native';

/**
 * Environment configuration for RentBook Mobile (Android Native & Expo).
 * 
 * Android Emulator: http://10.0.2.2:8000/api/v1
 * Physical Device / LAN: Configured via EXPO_PUBLIC_API_URL or ADB reverse
 */
const getDefaultApiUrl = (): string => {
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000/api/v1';
  }
  return 'http://localhost:8000/api/v1';
};

export const ENV = {
  API_BASE_URL: process.env.EXPO_PUBLIC_API_URL || getDefaultApiUrl(),
  IS_DEV: __DEV__,
} as const;
