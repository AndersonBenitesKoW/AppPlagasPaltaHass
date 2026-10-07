import { apiClient } from '../../../core/http/client';
import type { EnfermedadItem } from '../model/types';

export async function obtenerCatalogo(): Promise<EnfermedadItem[]> {
  const { data, error } = await apiClient.GET('/api/v1/catalogo');
  if (error) {
    throw new Error('Error al cargar catálogo');
  }
  return (data || []) as EnfermedadItem[];
}
