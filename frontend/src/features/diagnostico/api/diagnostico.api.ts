import { env } from '../../../core/config/env';
import type { Diagnostico, DiagnosticosBatchResponse } from '../model/types';

export type Organo = 'hoja' | 'fruto';

export async function enviarDiagnostico(
  file: File,
  organo: Organo = 'hoja',
): Promise<Diagnostico> {
  const formData = new FormData();
  formData.append('imagen', file);
  formData.append('organo', organo);

  const response = await fetch(`${env.apiBaseUrl}/api/v1/diagnosticos`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorJson = await response.json().catch(() => null);
    throw new Error(errorJson?.detail || 'Error al procesar la imagen con el modelo');
  }

  return (await response.json()) as Diagnostico;
}

export async function enviarDiagnosticoLote(
  files: File[],
  organo: Organo = 'hoja',
): Promise<DiagnosticosBatchResponse> {
  const formData = new FormData();

  for (const file of files) {
    formData.append('imagenes', file);
  }

  formData.append('organo', organo);

  const response = await fetch(`${env.apiBaseUrl}/api/v1/diagnosticos/batch`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorJson = await response.json().catch(() => null);
    throw new Error(errorJson?.detail || 'Error al procesar el lote de imágenes');
  }

  return (await response.json()) as DiagnosticosBatchResponse;
}
