import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AxiosError, AxiosHeaders } from 'axios';

/**
 * Create a wrapper with QueryClientProvider for testing hooks that use TanStack Query.
 * Uses retry: false to prevent test flakiness.
 */
export function createQueryWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return { wrapper: Wrapper, queryClient };
}

/**
 * Create an AxiosError for testing error handling.
 */
export function createAxiosError(
  status: number,
  data: any = {},
  config: any = {}
): AxiosError {
  const headers = new AxiosHeaders();
  const error = new AxiosError(
    `Request failed with status code ${status}`,
    String(status),
    config,
    {},
    {
      data,
      status,
      statusText: `Error ${status}`,
      headers,
      config: { headers } as any,
    }
  );
  return error;
}

/**
 * Create a network error (no response) for testing.
 */
export function createNetworkError(): AxiosError {
  const error = new AxiosError(
    'Network Error',
    'ERR_NETWORK',
    undefined,
    {}
  );
  // Ensure response is undefined (network error)
  (error as any).response = undefined;
  return error;
}

/**
 * Mock translation function that returns the key.
 */
export const mockT = (key: string) => key;
