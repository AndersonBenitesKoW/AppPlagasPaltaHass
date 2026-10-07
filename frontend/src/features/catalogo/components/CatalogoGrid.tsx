import React from 'react';
import { useCatalogo } from '../hooks/useCatalogo';
import { Card } from '../../../shared/ui/Card';
import { Badge, type BadgeVariant } from '../../../shared/ui/Badge';
import { BookOpen, AlertCircle, CheckCircle2 } from 'lucide-react';

function obtenerBadgeVariant(codigo: string): BadgeVariant {
  if (codigo.includes('sana') || codigo.includes('sano')) return 'sano';
  if (codigo.includes('antracnosis')) return 'antracnosis';
  if (codigo.includes('plaga')) return 'plaga';
  if (codigo.includes('deficiencia')) return 'deficiencia';
  return 'neutral';
}

export const CatalogoGrid: React.FC = () => {
  const { data: catalogo, isLoading, isError } = useCatalogo();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-400">
        <div className="animate-spin h-8 w-8 border-4 border-emerald-500 border-t-transparent rounded-full mr-3" />
        <span>Cargando catálogo agronómico...</span>
      </div>
    );
  }

  if (isError || !catalogo) {
    return (
      <div className="p-6 text-center text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-2xl">
        No se pudo cargar la información del catálogo.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
          <BookOpen className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-100">
            Guía de Plagas y Enfermedades en Palta Hass
          </h2>
          <p className="text-sm text-slate-400">
            Fichas técnicas de los patrones foliares identificados por el modelo de visión
            artificial.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {catalogo.map((item) => (
          <Card key={item.codigo} className="flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-start justify-between gap-4">
                <h3 className="text-lg font-bold text-slate-100">{item.nombre}</h3>
                <Badge variant={obtenerBadgeVariant(item.codigo)}>{item.severidad}</Badge>
              </div>

              <p className="text-sm text-slate-300 leading-relaxed">{item.descripcion}</p>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-400/90 mb-2 flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4" /> Síntomas identificables
                </h4>
                <ul className="text-xs text-slate-400 space-y-1.5 list-disc list-inside">
                  {item.sintomas.map((s, idx) => (
                    <li key={idx}>{s}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-emerald-400/90 mb-2 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> Recomendaciones de Manejo
                </h4>
                <ul className="text-xs text-slate-400 space-y-1.5 list-disc list-inside">
                  {item.recomendaciones.map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
