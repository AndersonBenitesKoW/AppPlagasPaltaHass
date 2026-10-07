export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface Deteccion {
  clase: string;
  confianza: number;
  caja: BoundingBox;
}

export interface Diagnostico {
  id: string;
  organo: string;
  propietario_id: string;
  es_sano: boolean;
  enfermedades: string[];
  detecciones: Deteccion[];
  imagen_url: string;
  creado_en: string;
  conclusiones?: {
    recomendaciones_agronomicas?: string[];
  };
}

export interface DiagnosticosBatchResponse {
  diagnosticos: Diagnostico[];
  total: number;
  total_enfermos: number;
  total_sanos: number;
}

export interface HistorialFiltros {
  desde?: string;
  hasta?: string;
  enfermedad?: string;
  limite?: number;
  offset?: number;
}
