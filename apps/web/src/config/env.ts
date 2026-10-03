/**
 * Environment configuration for RentBook Web.
 * Defaults to http://localhost:8000/api/v1 for local development.
 */
export const ENV = {
  API_BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  IS_PRODUCTION: import.meta.env.PROD,
  IS_DEVELOPMENT: import.meta.env.DEV,
} as const;
