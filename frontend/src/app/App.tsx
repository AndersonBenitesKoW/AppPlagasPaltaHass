import React, { useState } from 'react';
import { Navbar, type TabId } from './Navbar';
import {
  Dropzone,
  DiagnosticoDetalle,
  useDiagnosticar,
  type Diagnostico,
} from '../features/diagnostico';
import { HistorialLista, useHistorial } from '../features/historial';
import { CatalogoGrid } from '../features/catalogo';
import { Card } from '../shared/ui/Card';
import { Button } from '../shared/ui/Button';
import { Modal } from '../shared/ui/Modal';
import { Sparkles, RefreshCw, AlertCircle, Layers } from 'lucide-react';

export const App: React.FC = () => {
  const [tabActiva, setTabActiva] = useState<TabId>('analisis');
  const { analizarUno, analizarLote, isLoading, error } = useDiagnosticar();
  const { data: historial } = useHistorial();

  // Estado del resultado actual en vivo
  const [diagnosticosLote, setDiagnosticosLote] = useState<Diagnostico[]>([]);
  const [indiceLoteActivo, setIndiceLoteActivo] = useState<number>(0);
  const [diagnosticoHistorialModal, setDiagnosticoHistorialModal] = useState<Diagnostico | null>(
    null,
  );

  const handleAnalizar = async (archivos: File[]) => {
    try {
      if (archivos.length === 1) {
        const resultado = await analizarUno(archivos[0]);
        setDiagnosticosLote([resultado]);
        setIndiceLoteActivo(0);
      } else {
        const respuestaBatch = await analizarLote(archivos);
        setDiagnosticosLote(respuestaBatch.diagnosticos);
        setIndiceLoteActivo(0);
      }
    } catch {
      // Error manejado en el hook
    }
  };

  const nuevoAnalisis = () => {
    setDiagnosticosLote([]);
    setIndiceLoteActivo(0);
  };

  const diagnosticoActual = diagnosticosLote[indiceLoteActivo];

  return (
    <div className="min-h-screen flex flex-col bg-[#0a0f0d] text-slate-100">
      {/* Barra de navegación */}
      <Navbar
        tabActiva={tabActiva}
        onCambiarTab={setTabActiva}
        totalHistorial={historial?.length}
      />

      {/* Contenido principal */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* PESTAÑA: ANÁLISIS EN VIVO */}
        {tabActiva === 'analisis' && (
          <div className="space-y-10">
            {/* Cabecera / Hero */}
            <div className="text-center max-w-3xl mx-auto space-y-4">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
                <Sparkles className="w-3.5 h-3.5" />
                Detección por Visión Artificial • YOLO11
              </div>
              <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white leading-tight">
                Diagnóstico de Plagas y Enfermedades en{' '}
                <span className="text-emerald-400">Palta Hass</span>
              </h1>
              <p className="text-sm sm:text-base text-slate-400 leading-relaxed">
                Sube una o varias fotografías de hojas de palto para clasificar y delimitar
                automáticamente antracnosis, plagas foliares y deficiencias nutricionales mediante
                redes neuronales.
              </p>
            </div>

            {/* Error si ocurre */}
            {error && (
              <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3 max-w-2xl mx-auto">
                <AlertCircle className="w-5 h-5 shrink-0 text-rose-400" />
                <span>{error.message}</span>
              </div>
            )}

            {/* Si no hay diagnóstico actual: Dropzone */}
            {diagnosticosLote.length === 0 ? (
              <div className="max-w-3xl mx-auto">
                <Dropzone onAnalizar={handleAnalizar} isLoading={isLoading} />
              </div>
            ) : (
              /* Si ya hay resultados del análisis: Mostrar visor y selector si fue en lote */
              <div className="space-y-8 animate-fade-in">
                {/* Selector de lote si fueron múltiples imágenes */}
                {diagnosticosLote.length > 1 && (
                  <Card className="bg-[#121915] border-emerald-500/20">
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-dark-border">
                      <div className="flex items-center gap-2.5">
                        <Layers className="w-5 h-5 text-emerald-400" />
                        <div>
                          <h3 className="text-sm font-bold text-slate-200">
                            Lote de {diagnosticosLote.length} Muestras Foliares
                          </h3>
                          <span className="text-xs text-slate-400">
                            {diagnosticosLote.filter((d) => d.es_sano).length} Sanas •{' '}
                            {diagnosticosLote.filter((d) => !d.es_sano).length} Con Alerta
                          </span>
                        </div>
                      </div>

                      <Button variant="secondary" size="sm" onClick={nuevoAnalisis}>
                        <RefreshCw className="w-3.5 h-3.5 mr-1" /> Nuevo análisis
                      </Button>
                    </div>

                    {/* Miniaturas navegables */}
                    <div className="flex gap-3 overflow-x-auto pt-4 pb-2">
                      {diagnosticosLote.map((diag, idx) => (
                        <button
                          key={diag.id}
                          onClick={() => setIndiceLoteActivo(idx)}
                          className={`relative shrink-0 w-20 h-20 rounded-xl overflow-hidden border-2 transition-all cursor-pointer ${
                            idx === indiceLoteActivo
                              ? 'border-emerald-400 scale-105 shadow-lg shadow-emerald-500/20'
                              : 'border-dark-border opacity-60 hover:opacity-100'
                          }`}
                        >
                          <img
                            src={diag.imagen_url}
                            alt={`Muestra ${idx + 1}`}
                            className="w-full h-full object-cover"
                          />
                          <span
                            className={`absolute bottom-1 right-1 w-2.5 h-2.5 rounded-full ${
                              diag.es_sano ? 'bg-emerald-400' : 'bg-rose-500'
                            }`}
                          />
                        </button>
                      ))}
                    </div>
                  </Card>
                )}

                {/* Detalle de la imagen activa */}
                {diagnosticoActual && <DiagnosticoDetalle diagnostico={diagnosticoActual} />}

                {/* Botón para nuevo análisis si fue solo una imagen */}
                {diagnosticosLote.length === 1 && (
                  <div className="flex justify-center pt-4">
                    <Button variant="secondary" size="md" onClick={nuevoAnalisis}>
                      <RefreshCw className="w-4 h-4 mr-2" /> Analizar otra hoja o lote
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* PESTAÑA: HISTORIAL */}
        {tabActiva === 'historial' && (
          <HistorialLista onVerDetalle={(item) => setDiagnosticoHistorialModal(item)} />
        )}

        {/* PESTAÑA: GUÍA / CATÁLOGO */}
        {tabActiva === 'catalogo' && <CatalogoGrid />}

        {/* Modal de detalle para el Historial */}
        <Modal
          isOpen={Boolean(diagnosticoHistorialModal)}
          onClose={() => setDiagnosticoHistorialModal(null)}
          title="Detalle del Diagnóstico"
          className="max-w-4xl"
        >
          {diagnosticoHistorialModal && (
            <DiagnosticoDetalle diagnostico={diagnosticoHistorialModal} />
          )}
        </Modal>
      </main>

      {/* Pie de página */}
      <footer className="border-t border-emerald-500/10 bg-[#080d0a] py-8 text-center text-xs text-slate-500 space-y-2">
        <p>© 2026 PaltaVision • Ultralytics YOLO11 • FastAPI • React 19 • Tailwind CSS</p>
      </footer>
    </div>
  );
};
