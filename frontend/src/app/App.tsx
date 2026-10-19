import React, { useState } from 'react';
import { getApiUrl } from '../core/config/api-url';
import { Navbar, type TabId } from './Navbar';
import {
  Dropzone,
  CamaraTiempoReal,
  DiagnosticoDetalle,
  useDiagnosticar,
  type Diagnostico,
} from '../features/diagnostico';
import { HistorialLista, useHistorial } from '../features/historial';
import { CatalogoGrid } from '../features/catalogo';
import { Card } from '../shared/ui/Card';
import { Button } from '../shared/ui/Button';
import { Modal } from '../shared/ui/Modal';
import { Sparkles, RefreshCw, AlertCircle, Layers, Leaf, Apple } from 'lucide-react';
import type { Organo } from '../features/diagnostico/api/diagnostico.api';

export const App: React.FC = () => {
  const [tabActiva, setTabActiva] = useState<TabId>('analisis');
  const { analizarUno, analizarLote, isLoading, error } = useDiagnosticar();
  const { data: historial } = useHistorial();

  const [organoSeleccionado, setOrganoSeleccionado] = useState<Organo>('hoja');
  const [camaraAbierta, setCamaraAbierta] = useState(false);
  const [guardandoCamara, setGuardandoCamara] = useState(false);
  const [errorCamara, setErrorCamara] = useState<string | null>(null);

  // Estado del resultado actual en vivo
  const [diagnosticosLote, setDiagnosticosLote] = useState<Diagnostico[]>([]);
  const [indiceLoteActivo, setIndiceLoteActivo] = useState<number>(0);
  const [diagnosticoHistorialModal, setDiagnosticoHistorialModal] =
    useState<Diagnostico | null>(null);

  const handleAnalizar = async (archivos: File[]) => {
    try {
      if (archivos.length === 1) {
        const resultado = await analizarUno({
          file: archivos[0],
          organo: organoSeleccionado,
        });

        setDiagnosticosLote([resultado]);
        setIndiceLoteActivo(0);
      } else {
        const respuestaBatch = await analizarLote({
          files: archivos,
          organo: organoSeleccionado,
        });

        setDiagnosticosLote(respuestaBatch.diagnosticos);
        setIndiceLoteActivo(0);
      }
    } catch {
      // Error manejado en el hook
    }
  };

  const handleGuardarTiempoReal = async (archivo: File) => {
    setGuardandoCamara(true);
    setErrorCamara(null);
    try {
      // El backend vuelve a analizar el cuadro a resolución completa y lo guarda en la BD.
      const resultado = await analizarUno({ file: archivo, organo: organoSeleccionado });
      setDiagnosticosLote([resultado]);
      setIndiceLoteActivo(0);
      setCamaraAbierta(false);
    } catch (e) {
      setErrorCamara(e instanceof Error ? e.message : 'No se pudo guardar el diagnóstico.');
    } finally {
      setGuardandoCamara(false);
    }
  };

  const nuevoAnalisis = () => {
    setDiagnosticosLote([]);
    setIndiceLoteActivo(0);
  };

  const diagnosticoActual = diagnosticosLote[indiceLoteActivo];

  return (
    <div className="min-h-screen flex flex-col bg-[#0a0f0d] text-slate-100">
      <Navbar
        tabActiva={tabActiva}
        onCambiarTab={setTabActiva}
        totalHistorial={historial?.length}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {tabActiva === 'analisis' && (
          <div className="space-y-10">
            {/* Cabecera */}
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
                Apunta la cámara a una hoja o fruto de palto para detectar enfermedades en
                tiempo real, o sube una o varias fotografías para analizarlas.
              </p>
            </div>

            {/* Selector de órgano */}
            {diagnosticosLote.length === 0 && (
              <Card className="max-w-3xl mx-auto bg-[#121915] border-emerald-500/20">
                <div className="text-center mb-5">
                  <h2 className="text-base font-bold text-slate-200">
                    ¿Qué quieres analizar?
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Selecciona el tipo de muestra antes de subir las imágenes.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <button
                    type="button"
                    onClick={() => setOrganoSeleccionado('hoja')}
                    className={`p-5 rounded-2xl border-2 transition-all text-left ${
                      organoSeleccionado === 'hoja'
                        ? 'border-emerald-400 bg-emerald-500/10 shadow-lg shadow-emerald-500/10'
                        : 'border-slate-700 bg-slate-900/40 hover:border-emerald-500/40'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`p-3 rounded-xl ${
                          organoSeleccionado === 'hoja'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        <Leaf className="w-6 h-6" />
                      </div>

                      <div>
                        <h3 className="font-bold text-slate-200">Hoja</h3>
                        <p className="text-xs text-slate-400 mt-1">
                          Enfermedades y problemas foliares
                        </p>
                      </div>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => setOrganoSeleccionado('fruto')}
                    className={`p-5 rounded-2xl border-2 transition-all text-left ${
                      organoSeleccionado === 'fruto'
                        ? 'border-emerald-400 bg-emerald-500/10 shadow-lg shadow-emerald-500/10'
                        : 'border-slate-700 bg-slate-900/40 hover:border-emerald-500/40'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`p-3 rounded-xl ${
                          organoSeleccionado === 'fruto'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        <Apple className="w-6 h-6" />
                      </div>

                      <div>
                        <h3 className="font-bold text-slate-200">Fruto</h3>
                        <p className="text-xs text-slate-400 mt-1">
                          Enfermedades presentes en la palta
                        </p>
                      </div>
                    </div>
                  </button>
                </div>

                <div className="mt-5 text-center">
                  <span className="inline-flex items-center px-3 py-1 rounded-full bg-slate-800 text-xs text-slate-300">
                    Modelo seleccionado:{' '}
                    <strong className="ml-1 text-emerald-400">
                      {organoSeleccionado === 'hoja' ? 'hojas.pt' : 'frutos.pt'}
                    </strong>
                  </span>
                </div>
              </Card>
            )}

            {/* Error */}
            {error && (
              <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3 max-w-2xl mx-auto">
                <AlertCircle className="w-5 h-5 shrink-0 text-rose-400" />
                <span>{error.message}</span>
              </div>
            )}

            {/* Dropzone / resultados */}
            {diagnosticosLote.length === 0 ? (
              <div className="max-w-3xl mx-auto">
                <Dropzone
                  onAnalizar={handleAnalizar}
                  onAbrirCamara={() => {
                    setErrorCamara(null);
                    setCamaraAbierta(true);
                  }}
                  isLoading={isLoading}
                />
              </div>
            ) : (
              <div className="space-y-8 animate-fade-in">
                {/* Selector de lote */}
                {diagnosticosLote.length > 1 && (
                  <Card className="bg-[#121915] border-emerald-500/20">
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-dark-border">
                      <div className="flex items-center gap-2.5">
                        <Layers className="w-5 h-5 text-emerald-400" />

                        <div>
                          <h3 className="text-sm font-bold text-slate-200">
                            Lote de {diagnosticosLote.length}{' '}
                            {organoSeleccionado === 'hoja' ? 'Muestras Foliares' : 'Frutos'}
                          </h3>

                          <span className="text-xs text-slate-400">
                            {diagnosticosLote.filter((d) => d.es_sano).length} Sanas •{' '}
                            {diagnosticosLote.filter((d) => !d.es_sano).length} Con Alerta
                          </span>
                        </div>
                      </div>

                      <Button variant="secondary" size="sm" onClick={nuevoAnalisis}>
                        <RefreshCw className="w-3.5 h-3.5 mr-1" />
                        Nuevo análisis
                      </Button>
                    </div>

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
                            src={getApiUrl(diag.imagen_url)}
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

                {/* Detalle */}
                {diagnosticoActual && (
                  <DiagnosticoDetalle diagnostico={diagnosticoActual} />
                )}

                {/* Nuevo análisis */}
                {diagnosticosLote.length === 1 && (
                  <div className="flex justify-center pt-4">
                    <Button variant="secondary" size="md" onClick={nuevoAnalisis}>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Analizar otra hoja o fruto
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Historial */}
        {tabActiva === 'historial' && (
          <HistorialLista
            onVerDetalle={(item) => setDiagnosticoHistorialModal(item)}
          />
        )}

        {/* Catálogo */}
        {tabActiva === 'catalogo' && <CatalogoGrid />}

        {/* Cámara en tiempo real */}
        {camaraAbierta && (
          <CamaraTiempoReal
            organo={organoSeleccionado}
            guardando={guardandoCamara}
            errorGuardado={errorCamara}
            onGuardar={(archivo) => void handleGuardarTiempoReal(archivo)}
            onCerrar={() => setCamaraAbierta(false)}
          />
        )}

        {/* Modal historial */}
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

      {/* Footer */}
      <footer className="border-t border-emerald-500/10 bg-[#080d0a] py-8 text-center text-xs text-slate-500 space-y-2">
        <p>
          © 2026 PaltaVision • Ultralytics YOLO11 • FastAPI • React 19 • Tailwind CSS
        </p>
      </footer>
    </div>
  );
};

