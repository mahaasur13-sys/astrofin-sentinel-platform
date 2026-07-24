import { z } from 'zod';

const envSchema = z.object({
  VITE_API_URL: z.string().default('/api/v1'),
  VITE_SSE_URL: z.string().default('/api/v1/stream'),
  VITE_WS_URL: z.string().default('ws://localhost:8000/ws'),
  VITE_ENVIRONMENT: z.enum(['development', 'staging', 'production']).default('development'),
  VITE_SENTRY_DSN: z.string().optional(),
  VITE_DEBUG: z.coerce.boolean().default(false),
});

type Env = z.infer<typeof envSchema>;

function parseEnv(): Env {
  const raw = {
    VITE_API_URL: import.meta.env.VITE_API_URL,
    VITE_SSE_URL: import.meta.env.VITE_SSE_URL,
    VITE_WS_URL: import.meta.env.VITE_WS_URL,
    VITE_ENVIRONMENT: import.meta.env.VITE_ENVIRONMENT,
    VITE_SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN,
    VITE_DEBUG: import.meta.env.VITE_DEBUG,
  };

  const result = envSchema.safeParse(raw);
  if (!result.success) {
    console.warn('[Env] Invalid environment variables, using defaults', result.error.flatten());
    return envSchema.parse({});
  }
  return result.data;
}

export const env = parseEnv();
