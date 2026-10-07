import { env } from '../../../core/config/env';
import type { Diagnostico } from '../../../shared/types/diagnostico';

export async function obtenerHistorial(): Promise<Diagnostico[]> {
  const response = await fetch(`${env.apiBaseUrl}/api/v1/diagnosticos?limite=100`, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Error al obtener el historial de diagnósticos');
  }

  return (await response.json()) as Diagnostico[];
}
