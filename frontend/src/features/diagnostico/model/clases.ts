export interface PaletaClase {
  stroke: string;
  bg: string;
  text: string;
}

export const colorPorClase: Record<string, PaletaClase> = {
  hoja_sana: { stroke: '#10b981', bg: 'rgba(16, 185, 129, 0.25)', text: '#34d399' },
  antracnosis_hoja: { stroke: '#f43f5e', bg: 'rgba(244, 63, 94, 0.25)', text: '#fb7185' },
  plaga: { stroke: '#f59e0b', bg: 'rgba(245, 158, 11, 0.25)', text: '#fbbf24' },
  deficiencia_nutricional: { stroke: '#a855f7', bg: 'rgba(168, 85, 247, 0.25)', text: '#c084fc' },
  fruto_sano: { stroke: '#10b981', bg: 'rgba(16, 185, 129, 0.25)', text: '#34d399' },
  antracnosis_fruto: { stroke: '#f43f5e', bg: 'rgba(244, 63, 94, 0.25)', text: '#fb7185' },
  cercospora: { stroke: '#f97316', bg: 'rgba(249, 115, 22, 0.25)', text: '#fb923c' },
  rona: { stroke: '#eab308', bg: 'rgba(234, 179, 8, 0.25)', text: '#facc15' },
  pudricion_peduncular: { stroke: '#a855f7', bg: 'rgba(168, 85, 247, 0.25)', text: '#c084fc' },
  sunblotch: { stroke: '#ec4899', bg: 'rgba(236, 72, 153, 0.25)', text: '#f472b6' },
};

export const PALETA_POR_DEFECTO: PaletaClase = {
  stroke: '#38bdf8',
  bg: 'rgba(56, 189, 248, 0.25)',
  text: '#7dd3fc',
};

export function paletaDeClase(clase: string): PaletaClase {
  return colorPorClase[clase] ?? PALETA_POR_DEFECTO;
}

export function formatClase(clase: string): string {
  switch (clase) {
    case 'hoja_sana':
      return 'Hoja Sana';
    case 'antracnosis_hoja':
      return 'Antracnosis';
    case 'plaga':
      return 'Plaga (Trips/Ácaros)';
    case 'deficiencia_nutricional':
      return 'Deficiencia Nutricional';
    case 'fruto_sano':
      return 'Fruto Sano';
    case 'antracnosis_fruto':
      return 'Antracnosis';
    case 'cercospora':
      return 'Cercospora';
    case 'rona':
      return 'Roña';
    case 'pudricion_peduncular':
      return 'Pudrición Peduncular';
    case 'sunblotch':
      return 'Sunblotch';
    default:
      return clase.replace(/_/g, ' ');
  }
}

export function esClaseSana(clase: string): boolean {
  return clase === 'hoja_sana' || clase === 'fruto_sano';
}
