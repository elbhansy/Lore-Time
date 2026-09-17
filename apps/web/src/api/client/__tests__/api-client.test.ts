import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient, NormalizedApiError, classifyApiError } from '../api-client';

describe('ApiClient and Error Normalization', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('classifies network and 4xx/5xx errors accurately', () => {
    expect(classifyApiError(0, 'Failed to fetch')).toBe('NETWORK');
    expect(classifyApiError(404, 'Entity not found')).toBe('NOT_FOUND');
    expect(classifyApiError(400, 'Invalid chapter requested: chapter beyond boundary')).toBe('TEMPORAL_BOUNDARY');
    expect(classifyApiError(400, 'Missing field')).toBe('BAD_REQUEST');
    expect(classifyApiError(500, 'Internal Server Error')).toBe('SERVER_ERROR');
  });

  it('performs successful GET requests and parses JSON response', async () => {
    const mockData = { test: 'value', count: 42 };
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockData,
    }));

    const client = new ApiClient({ baseUrl: '/api/v1' });
    const result = await client.get<{ test: string; count: number }>('/test-endpoint');

    expect(globalThis.fetch).toHaveBeenCalledWith('/api/v1/test-endpoint', expect.objectContaining({
      method: 'GET',
    }));
    expect(result).toEqual(mockData);
  });

  it('normalizes HTTP 404 responses into NormalizedApiError', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ detail: 'Character not found at chapter' }),
    }));

    const client = new ApiClient();

    await expect(client.get('/characters/non-existent')).rejects.toThrow(NormalizedApiError);

    try {
      await client.get('/characters/non-existent');
    } catch (err: unknown) {
      const apiErr = err as NormalizedApiError;
      expect(apiErr.status).toBe(404);
      expect(apiErr.kind).toBe('NOT_FOUND');
      expect(apiErr.message).toBe('Character not found at chapter');
    }
  });

  it('normalizes temporal boundary errors into TEMPORAL_BOUNDARY kind', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => ({ detail: 'Requested chapter exceeds temporal horizon' }),
    }));

    const client = new ApiClient();

    try {
      await client.get('/timeline');
    } catch (err: unknown) {
      const apiErr = err as NormalizedApiError;
      expect(apiErr.status).toBe(422);
      expect(apiErr.kind).toBe('TEMPORAL_BOUNDARY');
    }
  });
});
