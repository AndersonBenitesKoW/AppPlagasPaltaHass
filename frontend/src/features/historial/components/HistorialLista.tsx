import React, { useState } from 'react';
import { useHistorial } from '../hooks/useHistorial';
import { Card } from '../../../shared/ui/Card';
import { Badge, type BadgeVariant } from '../../../shared/ui/Badge';
import { Button } from '../../../shared/ui/Button';
import type { Diagnostico } from '../../../shared/types/diagnostico';
import { History, Calendar, CheckCircle2, AlertTriangle, Search } from 'lucide-react';
import { getApiUrl } from '../../../core/config/api-url';

function getBadgeVariant(enfermedad: string): BadgeVariant {
  if (enfermedad.includes('sana') || enfermedad.includes('sano')) return 'sano';
  if (enfermedad.includes('antracnosis')) return 'antracnosis';
  if (enfermedad.includes('plaga')) return 'plaga';
  if (enfermedad.includes('deficiencia')) return 'deficiencia';
  return 'neutral';
}

function formatearNombre(codigo: string): string {
  switch (codigo) {
    case 'antracnosis_hoja':
      return 'Antracnosis';
    case 'plaga':
      return 'Plaga (Trips/Ácaros)';
    case 'deficiencia_nutricional':
      return 'Deficiencia';
    case 'hoja_sana':
      return 'Sana';
    default:
      return codigo;
  }
}

export interface HistorialListaProps {
  onVerDetalle?: (diagnostico: Diagnostico) => void;
}

export const HistorialLista: React.FC<HistorialListaProps> = ({ onVerDetalle }) => {
  const { data: historial, isLoading, isError, refetch } = useHistorial();
  const [filtro, setFiltro] = useState<'todos' | 'enfermos' | 'sanos'>('todos');

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-16 text-slate-400 space-y-3">
        <div className="animate-spin h-9 w-9 border-4 border-emerald-500 border-t-transparent rounded-full" />
        <span className="text-sm font-medium">Cargando historial de la base de datos...</span>
      </div>
    );
  }

  if (isError || !historial) {
    return (
      <div className="p-8 text-center bg-rose-500/10 border border-rose-500/20 rounded-3xl space-y-3">
        <p className="text-rose-400 font-medium">No se pudo cargar el historial de diagnósticos.</p>
        <Button variant="secondary" size="sm" onClick={() => refetch()}>
          Reintentar
        </Button>
      </div>
    );
  }

  const itemsFiltrados = historial.filter((item) => {
    if (filtro === 'enfermos') return !item.es_sano;
    if (filtro === 'sanos') return item.es_sano;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Cabecera y controles de filtro */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-dark-border">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100">
              Historial de Diagnósticos Registrados
            </h2>
            <p className="text-xs text-slate-400">
              {historial.length} análisis almacenados en la base de datos
            </p>
          </div>
        </div>

        {/* Filtros */}
        <div className="flex items-center gap-1.5 p-1 bg-black/40 rounded-xl border border-dark-border self-stretch sm:self-auto">
          <button
            onClick={() => setFiltro('todos')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              filtro === 'todos'
                ? 'bg-emerald-500 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Todos ({historial.length})
          </button>
          <button
            onClick={() => setFiltro('enfermos')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              filtro === 'enfermos'
                ? 'bg-rose-500 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Con Alerta ({historial.filter((h) => !h.es_sano).length})
          </button>
          <button
            onClick={() => setFiltro('sanos')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              filtro === 'sanos'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Sanos ({historial.filter((h) => h.es_sano).length})
          </button>
        </div>
      </div>

      {/* Grid del historial */}
      {itemsFiltrados.length === 0 ? (
        <div className="p-12 text-center rounded-3xl border border-dark-border bg-[#121915]/40 space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center text-slate-400 mx-auto">
            <Search className="w-6 h-6" />
          </div>
          <p className="text-base font-semibold text-slate-300">
            No hay registros para este filtro
          </p>
          <p className="text-xs text-slate-500">
            Realiza un análisis en vivo de una o varias hojas para almacenar los resultados.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {itemsFiltrados.map((item) => (
            <Card
              key={item.id}
              className="group overflow-hidden flex flex-col justify-between border-dark-border hover:border-emerald-500/40 cursor-pointer"
              onClick={() => onVerDetalle?.(item)}
            >
              <div className="space-y-4">
                {/* Miniatura y badge superpuesto */}
                <div className="relative aspect-video rounded-xl overflow-hidden bg-black/50 border border-dark-border">
                  <img
  src={getApiUrl(item.imagen_url)}
  alt="Hoja analizada"
  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
/>
                  <div className="absolute top-2.5 left-2.5">
                    {item.es_sano ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/90 text-white backdrop-blur-md shadow-md">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Sano
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/90 text-white backdrop-blur-md shadow-md">
                        <AlertTriangle className="w-3.5 h-3.5" /> Alerta
                      </span>
                    )}
                  </div>
                  <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/75 text-[11px] text-slate-300 font-mono">
                    {item.detecciones.length} cajas
                  </div>
                </div>

                {/* Info */}
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5 text-xs text-slate-400">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>
                      {new Date(item.creado_en).toLocaleString('es-PE', {
                        dateStyle: 'medium',
                        timeStyle: 'short',
                      })}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {item.enfermedades.length === 0 ? (
                      <Badge variant="sano">Hoja Sana</Badge>
                    ) : (
                      item.enfermedades.map((enf) => (
                        <Badge key={enf} variant={getBadgeVariant(enf)}>
                          {formatearNombre(enf)}
                        </Badge>
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* Botón ver detalle */}
              <div className="pt-4 mt-4 border-t border-dark-border flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-emerald-400 group-hover:text-emerald-300"
                  onClick={(e) => {
                    e.stopPropagation();
                    onVerDetalle?.(item);
                  }}
                >
                  Ver Detecciones →
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
