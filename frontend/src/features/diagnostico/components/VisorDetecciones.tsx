import React, { useState } from 'react';
import type { Deteccion } from '../model/types';
import { Eye, EyeOff } from 'lucide-react';

interface VisorDeteccionesProps {
  imagenUrl: string;
  detecciones: Deteccion[];
  className?: string;
}

const colorPorClase: Record<string, { stroke: string; bg: string; text: string }> = {
  hoja_sana: { stroke: '#10b981', bg: 'rgba(16, 185, 129, 0.25)', text: '#34d399' },
  antracnosis_hoja: { stroke: '#f43f5e', bg: 'rgba(244, 63, 94, 0.25)', text: '#fb7185' },
  plaga: { stroke: '#f59e0b', bg: 'rgba(245, 158, 11, 0.25)', text: '#fbbf24' },
  deficiencia_nutricional: { stroke: '#a855f7', bg: 'rgba(168, 85, 247, 0.25)', text: '#c084fc' },
};

function formatClase(clase: string): string {
  switch (clase) {
    case 'hoja_sana':
      return 'Hoja Sana';
    case 'antracnosis_hoja':
      return 'Antracnosis';
    case 'plaga':
      return 'Plaga (Trips/Ácaros)';
    case 'deficiencia_nutricional':
      return 'Deficiencia Nutricional';
    default:
      return clase.replace(/_/g, ' ');
  }
}

export const VisorDetecciones: React.FC<VisorDeteccionesProps> = ({
  imagenUrl,
  detecciones,
  className = '',
}) => {
  const [mostrarCajas, setMostrarCajas] = useState(true);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  return (
    <div
      className={`relative rounded-2xl overflow-hidden bg-black/60 border border-dark-border group ${className}`}
    >
      {/* Botón flotante para alternar cajas */}
      <div className="absolute top-3 right-3 z-20">
        <button
          onClick={() => setMostrarCajas(!mostrarCajas)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-black/70 hover:bg-black/90 text-xs font-medium text-slate-200 border border-white/10 backdrop-blur-md transition-all shadow-lg cursor-pointer"
          title={mostrarCajas ? 'Ocultar cajas de detección' : 'Mostrar cajas de detección'}
        >
          {mostrarCajas ? (
            <EyeOff className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <Eye className="w-3.5 h-3.5" />
          )}
          <span>{mostrarCajas ? 'Ocultar cajas' : 'Ver cajas'}</span>
        </button>
      </div>

      {/* Contenedor relativo de imagen y overlay SVG */}
      <div className="relative w-full aspect-square max-h-[500px] flex items-center justify-center overflow-hidden">
        <img src={imagenUrl} alt="Hoja analizada" className="w-full h-full object-contain" />

        {mostrarCajas && (
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
          >
            {detecciones.map((det, idx) => {
              const paleta = colorPorClase[det.clase] || {
                stroke: '#38bdf8',
                bg: 'rgba(56, 189, 248, 0.25)',
                text: '#7dd3fc',
              };
              const isHovered = hoverIndex === idx;

              const x = det.caja.x1 * 100;
              const y = det.caja.y1 * 100;
              const width = (det.caja.x2 - det.caja.x1) * 100;
              const height = (det.caja.y2 - det.caja.y1) * 100;

              return (
                <g
                  key={idx}
                  onMouseEnter={() => setHoverIndex(idx)}
                  onMouseLeave={() => setHoverIndex(null)}
                >
                  {/* Bounding Box */}
                  <rect
                    x={x}
                    y={y}
                    width={width}
                    height={height}
                    fill={paleta.bg}
                    stroke={paleta.stroke}
                    strokeWidth={isHovered ? '0.8' : '0.5'}
                    strokeDasharray={det.clase === 'hoja_sana' ? 'none' : '1.5, 0.8'}
                    rx="1"
                    className="transition-all duration-150"
                  />

                  {/* Etiqueta flotante con clase y porcentaje */}
                  <g transform={`translate(${x}, ${Math.max(3, y - 1)})`}>
                    <rect
                      x="0"
                      y="-3.8"
                      width={Math.max(14, formatClase(det.clase).length * 1.5 + 8)}
                      height="4.2"
                      fill={paleta.stroke}
                      rx="0.8"
                      className="shadow-sm opacity-95"
                    />
                    <text
                      x="1"
                      y="-0.8"
                      fill="#ffffff"
                      fontSize="2.4"
                      fontWeight="bold"
                      fontFamily="sans-serif"
                    >
                      {formatClase(det.clase)} {(det.confianza * 100).toFixed(1)}%
                    </text>
                  </g>
                </g>
              );
            })}
          </svg>
        )}
      </div>

      {/* Barra de conteo de detecciones */}
      <div className="p-3 bg-[#111915] border-t border-dark-border flex items-center justify-between text-xs text-slate-400">
        <span className="font-medium text-slate-300">
          {detecciones.length === 0
            ? 'Sin detecciones de plaga/enfermedad'
            : `${detecciones.length} detección(es) encontradas por el modelo`}
        </span>
        <div className="flex gap-2">
          {Array.from(new Set(detecciones.map((d) => d.clase))).map((clase) => {
            const paleta = colorPorClase[clase] || { stroke: '#38bdf8', text: '#7dd3fc' };
            return (
              <span
                key={clase}
                className="px-2 py-0.5 rounded-md font-semibold text-[11px]"
                style={{ backgroundColor: `${paleta.stroke}20`, color: paleta.text }}
              >
                {formatClase(clase)}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
};
