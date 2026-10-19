import { z } from 'zod';

declare global {
  interface Window {
    __APP_CONFIG__?: {
      apiBaseUrl?: string;
      authUrl?: string;
      env?: string;
    };
  }
}

const EnvSchema = z.object({
  apiBaseUrl: z.string().url(),
  authUrl: z.string().url().optional(),
  env: z.enum(['dev', 'staging', 'prod']).default('dev'),
});

const runtimeConfig = typeof window !== 'undefined' ? window.__APP_CONFIG__ : undefined;

export const env = EnvSchema.parse({
  apiBaseUrl:
    import.meta.env.VITE_API_BASE_URL || runtimeConfig?.apiBaseUrl || 'http://localhost:8000',
  authUrl:
    runtimeConfig?.authUrl ||
    import.meta.env.VITE_AUTH_URL ||
    'http://localhost:8081/realms/plagas',
  env: runtimeConfig?.env || import.meta.env.VITE_APP_ENV || 'dev',
});