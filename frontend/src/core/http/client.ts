import createClient, { type Middleware } from 'openapi-fetch';
import type { paths } from './schema';
import { env } from '../config/env';
import { ApiError } from './api-error';

const errorMiddleware: Middleware = {
  async onResponse({ response }) {
    if (!response.ok) {
      const body = await response
        .clone()
        .json()
        .catch(() => null);
      throw ApiError.desde(body, response.status);
    }
  },
};

export const apiClient = createClient<paths>({
  baseUrl: env.apiBaseUrl,
});

apiClient.use(errorMiddleware);
