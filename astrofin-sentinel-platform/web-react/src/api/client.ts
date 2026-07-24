import { z } from 'zod';
import type { ApiErrorResponse, ApiResponse } from '@/types/api';

const BASE_URL = import.meta.env.VITE_API_URL ?? '';

interface RequestOptions {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

function jitter(ms: number): number {
  return ms + Math.random() * ms * 0.5;
}

function isSafeMethod(method: string): boolean {
  return ['GET', 'HEAD', 'OPTIONS'].includes(method);
}

export class ApiError extends Error {
  code: string;
  status: number;
  correlationId: string;

  constructor(err: ApiErrorResponse) {
    super(err.message);
    this.name = 'ApiError';
    this.code = err.code;
    this.status = err.status;
    this.correlationId = err.correlation_id;
  }
}

async function request<T>(
  path: string,
  opts: RequestOptions = {},
): Promise<ApiResponse<T>> {
  const { method = 'GET', body, signal } = opts;

  const headers: Record<string, string> = { ...opts.headers };

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  if (!isSafeMethod(method)) {
    headers['X-CSRF-Protection'] = '1';
  }
  headers['X-Requested-With'] = 'XMLHttpRequest';

  let retries = 2;
  let lastError: unknown;

  while (retries >= 0) {
    try {
      const resp = await fetch(`${BASE_URL}${path}`, {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
        credentials: 'same-origin',
        signal,
      });

      if (!resp.ok) {
        const errBody: ApiErrorResponse = await resp.json().catch(() => ({
          code: 'UNKNOWN',
          message: resp.statusText,
          trace_id: '',
          correlation_id: '',
          status: resp.status,
        }));
        throw new ApiError(errBody);
      }

      return await resp.json();
    } catch (err) {
      if (err instanceof ApiError) throw err;
      if (retries === 0) throw err;
      lastError = err;
      retries -= 1;
      await new Promise((r) => setTimeout(r, jitter(500 * (2 - retries))));
    }
  }

  throw lastError;
}

export const apiClient = {
  get: <T>(path: string, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: 'GET' }),

  post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: 'POST', body }),

  put: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: 'PUT', body }),

  delete: <T>(path: string, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: 'DELETE', ...opts }),
};

export async function get<T>(
  schema: z.ZodType<T>,
  path: string,
  opts?: RequestOptions,
): Promise<T> {
  const resp = await apiClient.get<T>(path, opts);
  return schema.parse(resp.data);
}

export async function post<T>(
  schema: z.ZodType<T>,
  path: string,
  body?: unknown,
  opts?: RequestOptions,
): Promise<T> {
  const resp = await apiClient.post<T>(path, body, opts);
  return schema.parse(resp.data);
}
