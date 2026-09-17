/**
 * Phase 6.1 API Client & Error Normalization.
 * 
 * Provides:
 * - Centralized fetch wrapper
 * - Normalized ApiError with error kinds (NETWORK, NOT_FOUND, SERVER_ERROR, CLIENT_ERROR, TEMPORAL_BOUNDARY)
 * - Base URL configuration via env / config
 * - Request cancellation via AbortSignal
 * - Strict series isolation & temporal parameter requirements
 */

export type ApiErrorKind = 
  | 'NETWORK'
  | 'NOT_FOUND'
  | 'BAD_REQUEST'
  | 'TEMPORAL_BOUNDARY'
  | 'SERVER_ERROR'
  | 'UNKNOWN';

export class NormalizedApiError extends Error {
  public readonly kind: ApiErrorKind;
  public readonly status: number;
  public readonly details?: unknown;

  constructor(status: number, message: string, kind: ApiErrorKind, details?: unknown) {
    super(message);
    this.name = 'NormalizedApiError';
    this.status = status;
    this.kind = kind;
    this.details = details;
  }
}

export function classifyApiError(status: number, message: string): ApiErrorKind {
  if (status === 0 || !status) return 'NETWORK';
  if (status === 404) return 'NOT_FOUND';
  if (status === 400 || status === 422) {
    if (message.toLowerCase().includes('temporal') || message.toLowerCase().includes('chapter')) {
      return 'TEMPORAL_BOUNDARY';
    }
    return 'BAD_REQUEST';
  }
  if (status >= 500) return 'SERVER_ERROR';
  return 'UNKNOWN';
}

export interface ApiClientConfig {
  baseUrl?: string;
  defaultHeaders?: Record<string, string>;
  timeoutMs?: number;
}

const DEFAULT_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) 
  ? String(import.meta.env.VITE_API_URL) 
  : '/api/v1';

export class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;
  private timeoutMs: number;

  constructor(config: ApiClientConfig = {}) {
    this.baseUrl = config.baseUrl ?? DEFAULT_BASE_URL;
    this.defaultHeaders = config.defaultHeaders ?? {};
    this.timeoutMs = config.timeoutMs ?? 15000;
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...this.defaultHeaders,
      ...(options.headers as Record<string, string>),
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);
    const signal = options.signal || controller.signal;

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorMessage = response.statusText || 'Request failed';
        let details: unknown = undefined;
        try {
          const body = await response.json();
          details = body;
          errorMessage = body.detail || body.message || errorMessage;
        } catch {
          // not JSON
        }
        const kind = classifyApiError(response.status, errorMessage);
        throw new NormalizedApiError(response.status, errorMessage, kind, details);
      }

      return (await response.json()) as T;
    } catch (err: unknown) {
      clearTimeout(timeoutId);

      if (err instanceof NormalizedApiError) {
        throw err;
      }

      const isAbort = (err as { name?: string })?.name === 'AbortError';
      const msg = isAbort ? 'Request timed out' : ((err as Error)?.message || 'Network error');
      throw new NormalizedApiError(0, msg, 'NETWORK', err);
    }
  }

  public get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  public post<T>(endpoint: string, body?: unknown, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }
}

export const defaultApiClient = new ApiClient();
