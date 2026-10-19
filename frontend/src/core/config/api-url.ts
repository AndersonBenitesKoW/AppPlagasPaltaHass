import { env } from './env';

export function getApiUrl(path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }

  return `${env.apiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`;
}