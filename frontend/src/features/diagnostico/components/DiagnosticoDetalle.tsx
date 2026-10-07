import React from 'react';
import type { Diagnostico } from '../model/types';
import { VisorDetecciones } from './VisorDetecciones';
import { Badge, type BadgeVariant } from '../../../shared/ui/Badge';
import { Card } from '../../../shared/ui/Card';
import { CheckCircle2, AlertTriangle, ShieldCheck, Calendar, Info } from 'lucide-react';

interface DiagnosticoDetalleProps {
  diagnostico: Diagnostico;
}

function getBadgeVariant(enfermedad: string): BadgeVariant {
  if (enfermedad.includes('sana') || enfermedad.includes('sano')) return 'sano';
  if (enfermedad.includes('antracnosis')) return 'antracnosis';
  if (enfermedad.includes('plaga')) return 'plaga';
  if (enfermedad.includes('deficiencia')) return 'deficiencia';
  return 'neutral';
}

function nombreFormateado(codigo: string): string {
  switch (codigo) {
    case 'antracnosis_hoja':
      return 'Antracnosis en Hoja (Colletotrichum)';
    case 'plaga':
      return 'Afección por Plagas (Trips / Ácaros)';
    case 'deficiencia_nutricional':
      return 'Deficiencia Nutricional (Clorosis)';
    case 'hoja_sana':
      return 'Follaje Sano';
    default:
      return codigo.replace(/_/g, ' ');
  }
}

export const DiagnosticoDetalle: React.FC<DiagnosticoDetalleProps> = ({ diagnostico }) => {
  const recomendaciones =
    diagnostico.conclusiones?.recomendaciones_agronomicas &&
    diagnostico.conclusiones.recomendaciones_agronomicas.length > 0
      ? diagnostico.conclusiones.recomendaciones_agronomicas
      : [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      {/* Columna Izquierda: Visor con Bounding Boxes */}
      <div className="lg:col-span-7 space-y-4">
        <VisorDetecciones
          imagenUrl={diagnostico.imagen_url}
          detecciones={diagnostico.detecciones}
        />
        <div className="flex items-center justify-between text-xs text-slate-400 px-2">
          <span className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" />
            {new Date(diagnostico.creado_en).toLocaleString('es-PE', {
              dateStyle: 'medium',
              timeStyle: 'short',
            })}
          </span>
          <span className="text-slate-500 font-mono text-[11px]">
            ID: {diagnostico.id.slice(0, 8)}...
          </span>
        </div>
      </div>

      {/* Columna Derecha: Panel de Veredicto y Recomendaciones */}
      <div className="lg:col-span-5 space-y-6">
        {/* Veredicto General */}
        <Card className="border border-emerald-500/20 bg-[#121915]/90">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              {diagnostico.es_sano ? (
                <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
                  <ShieldCheck className="w-7 h-7" />
                </div>
              ) : (
                <div className="w-12 h-12 rounded-2xl bg-rose-500/20 text-rose-400 flex items-center justify-center border border-rose-500/30">
                  <AlertTriangle className="w-7 h-7" />
                </div>
              )}
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Veredicto del Modelo YOLO11
                </span>
                <h3 className="text-xl font-bold text-slate-100">
                  {diagnostico.es_sano
                    ? 'Hoja en Estado Saludable'
                    : 'Alerta Fitosanitaria Detectada'}
                </h3>
              </div>
            </div>

            <p className="text-sm text-slate-300 leading-relaxed">
              {diagnostico.es_sano
                ? 'No se registraron signos patológicos significativos en la muestra foliar analizada. Las cajas del modelo confirman un área foliar sin invasión de plagas ni necrosis.'
                : 'Se identificaron anomalías foliares compatibles con agentes bióticos o abióticos que requieren intervención agronómica.'}
            </p>

            {/* Lista de enfermedades */}
            <div className="pt-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Clasificación de Detecciones
              </span>
              <div className="flex flex-wrap gap-2">
                {diagnostico.enfermedades.length === 0 ? (
                  <Badge variant="sano">Hoja Sana</Badge>
                ) : (
                  diagnostico.enfermedades.map((enf) => (
                    <Badge key={enf} variant={getBadgeVariant(enf)}>
                      {nombreFormateado(enf)}
                    </Badge>
                  ))
                )}
              </div>
            </div>
          </div>
        </Card>

        {/* Recomendaciones agronómicas */}
        <Card className="border border-dark-border bg-[#101713]/80 space-y-4">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
            <Info className="w-4 h-4" />
            <span>Acciones Recomendadas</span>
          </div>

          {recomendaciones.length > 0 ? (
            <ul className="space-y-2 text-xs text-slate-300">
              {recomendaciones.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-400">
              Mantener el programa habitual de riego y fertilización. Monitorear periódicamente el
              dosel del árbol para detectar oportunamente cualquier cambio en la coloración foliar.
            </p>
          )}
        </Card>
      </div>
    </div>
  );
};
