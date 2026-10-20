import { env } from '../../../core/config/env';
import type { Diagnostico } from '../../../shared/types/diagnostico';

const BASE = `${env.apiBaseUrl}/api/v1/diagnosticos`;

async function exigirOk(response: Response, mensaje: string): Promise<void> {
  if (!response.ok) {
    const errorJson = await response.json().catch(() => null);
    throw new Error(errorJson?.detail || mensaje);
  }
}

export async function obtenerHistorial(): Promise<Diagnostico[]> {
  const response = await fetch(`${BASE}?limite=100`, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Error al obtener el historial de diagnósticos');
  }

  return (await response.json()) as Diagnostico[];
}

export async function obtenerPapelera(): Promise<Diagnostico[]> {
  const response = await fetch(`${BASE}/papelera?limite=100`, {
    headers: { Accept: 'application/json' },
  });
  await exigirOk(response, 'Error al obtener la papelera');
  return (await response.json()) as Diagnostico[];
}

/** Mueve el diagnóstico a la papelera (se puede restaurar). */
export async function eliminarDiagnostico(id: string): Promise<void> {
  const response = await fetch(`${BASE}/${id}`, { method: 'DELETE' });
  await exigirOk(response, 'Error al mover el diagnóstico a la papelera');
}

export async function restaurarDiagnostico(id: string): Promise<Diagnostico> {
  const response = await fetch(`${BASE}/${id}/restaurar`, { method: 'POST' });
  await exigirOk(response, 'Error al restaurar el diagnóstico');
  return (await response.json()) as Diagnostico;
}

/** Borra el registro y su imagen de forma permanente. */
export async function eliminarDefinitivo(id: string): Promise<void> {
  const response = await fetch(`${BASE}/${id}/definitivo`, { method: 'DELETE' });
  await exigirOk(response, 'Error al eliminar definitivamente el diagnóstico');
}

export async function vaciarPapelera(): Promise<{ eliminados: number }> {
  const response = await fetch(`${BASE}/papelera`, { method: 'DELETE' });
  await exigirOk(response, 'Error al vaciar la papelera');
  return (await response.json()) as { eliminados: number };
}
