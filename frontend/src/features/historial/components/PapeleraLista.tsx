import React, { useState } from 'react';
import {
  usePapelera,
  useEliminarDefinitivo,
  useRestaurarDiagnostico,
  useVaciarPapelera,
} from '../hooks/usePapelera';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import type { Diagnostico } from '../../../shared/types/diagnostico';
import {
  Trash2,
  RotateCcw,
  ArrowLeft,
  Camera,
  Database,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { getApiUrl } from '../../../core/config/api-url';

function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short' });
}

export interface PapeleraListaProps {
  onVolver: () => void;
}

export const PapeleraLista: React.FC<PapeleraListaProps> = ({ onVolver }) => {
  const { data: papelera, isLoading, isError, refetch } = usePapelera();
  const restaurar = useRestaurarDiagnostico();
  const eliminar = useEliminarDefinitivo();
  const vaciar = useVaciarPapelera();
  const [errorAccion, setErrorAccion] = useState<string | null>(null);

  const alFallar = (mensaje: string) => () => setErrorAccion(mensaje);

  const confirmarEliminar = (item: Diagnostico) => {
    if (
      !window.confirm(
        `¿Eliminar DEFINITIVAMENTE el registro del ${formatearFecha(item.creado_en)}?\n` +
          'Se borrará la imagen y el diagnóstico. No se puede deshacer.',
      )
    ) {
      return;
    }
    setErrorAccion(null);
    eliminar.mutate(item.id, { onError: alFallar('No se pudo eliminar el registro.') });
  };

  const confirmarVaciar = () => {
    if (
      !window.confirm(
        `¿Vaciar la papelera? Se eliminarán definitivamente ${papelera?.length ?? 0} registros con sus imágenes. No se puede deshacer.`,
      )
    ) {
      return;
    }
    setErrorAccion(null);
    vaciar.mutate(undefined, { onError: alFallar('No se pudo vaciar la papelera.') });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-dark-border">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
            <Trash2 className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100">Papelera</h2>
            <p className="text-xs text-slate-400">
              Los registros aquí no aparecen en el historial. Puedes restaurarlos o eliminarlos
              definitivamente.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-stretch sm:self-auto">
          <Button variant="secondary" size="sm" onClick={onVolver}>
            <ArrowLeft className="w-3.5 h-3.5" />
            Volver al historial
          </Button>
          <Button
            variant="danger"
            size="sm"
            disabled={!papelera || papelera.length === 0}
            isLoading={vaciar.isPending}
            onClick={confirmarVaciar}
          >
            <Trash2 className="w-3.5 h-3.5" />
            Vaciar papelera
          </Button>
        </div>
      </div>

      {errorAccion && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
          {errorAccion}
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center p-16">
          <div className="animate-spin h-9 w-9 border-4 border-emerald-500 border-t-transparent rounded-full" />
        </div>
      ) : isError || !papelera ? (
        <div className="p-8 text-center bg-rose-500/10 border border-rose-500/20 rounded-3xl space-y-3">
          <p className="text-rose-400 font-medium">No se pudo cargar la papelera.</p>
          <Button variant="secondary" size="sm" onClick={() => refetch()}>
            Reintentar
          </Button>
        </div>
      ) : papelera.length === 0 ? (
        <div className="p-12 text-center rounded-3xl border border-dark-border bg-[#121915]/40 space-y-2">
          <p className="text-base font-semibold text-slate-300">La papelera está vacía</p>
          <p className="text-xs text-slate-500">
            Los registros que elimines del historial aparecerán aquí.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {papelera.map((item) => (
            <Card
              key={item.id}
              className="overflow-hidden flex flex-col justify-between border-dark-border"
            >
              <div className="space-y-3">
                <div className="relative aspect-video rounded-xl overflow-hidden bg-black/50 border border-dark-border">
                  <img
                    src={getApiUrl(item.imagen_url)}
                    alt="Muestra en la papelera"
                    className="w-full h-full object-cover opacity-60 grayscale"
                  />
                  <div className="absolute top-2.5 left-2.5">
                    {item.es_sano ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/90 text-white">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Sano
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/90 text-white">
                        <AlertTriangle className="w-3.5 h-3.5" /> Alerta
                      </span>
                    )}
                  </div>
                  <div className="absolute top-2.5 right-2.5 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-black/75 text-slate-200">
                    {item.origen === 'campo' ? (
                      <>
                        <Camera className="w-3 h-3" /> Campo
                      </>
                    ) : (
                      <>
                        <Database className="w-3 h-3" /> Dataset
                      </>
                    )}
                  </div>
                </div>
                <div className="text-xs text-slate-400 space-y-1">
                  <p>Analizado: {formatearFecha(item.creado_en)}</p>
                  {item.eliminado_en && (
                    <p className="text-rose-300/80">
                      En papelera desde: {formatearFecha(item.eliminado_en)}
                    </p>
                  )}
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-dark-border flex items-center justify-between gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  isLoading={restaurar.isPending && restaurar.variables === item.id}
                  onClick={() => {
                    setErrorAccion(null);
                    restaurar.mutate(item.id, {
                      onError: alFallar('No se pudo restaurar el registro.'),
                    });
                  }}
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Restaurar
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  isLoading={eliminar.isPending && eliminar.variables === item.id}
                  onClick={() => confirmarEliminar(item)}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  Eliminar definitivamente
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
