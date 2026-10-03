import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  define: {
    __DEV__: true,
  },
  resolve: {
    alias: {
      'react-native': path.resolve(__dirname, './src/test/react-native-mock.ts'),
      'expo-secure-store': path.resolve(__dirname, './src/test/expo-secure-store-mock.ts'),
    },
  },
  test: {
    environment: 'node',
    globals: true,
  },
});
