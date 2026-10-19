import React, { useEffect, useRef, useState } from 'react';
import { Camera, CheckCircle2, Loader2, RotateCcw, Save, ScanSearch, X } from 'lucide-react';

import type { Organo } from '../api/diagnostico.api';
import { useDetectorTiempoReal } from '../hooks/useDetectorTiempoReal';
import { esClaseSana, formatClase, paletaDeClase } from '../model/clases';

interface CamaraTiempoRealProps {
  organo: Organo;
  guardando: boolean;
  errorGuardado?: string | null;
  onGuardar: (archivo: File) => void;
  onCerrar: () => void;
}

// Por debajo de este tamaño (fracción del cuadro) el objeto está muy lejos para el modelo.
const AREA_MINIMA_OBJETO = 0.03;

export const CamaraTiempoReal: React.FC<CamaraTiempoRealProps> = ({
  organo,
  guardando,
  errorGuardado,
  onGuardar,
  onCerrar,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [camaraActiva, setCamaraActiva] = useState<'environment' | 'user'>('environment');
  const [errorCamara, setErrorCamara] = useState<string | null>(null);
  const [dimVideo, setDimVideo] = useState<{ w: number; h: number } | null>(null);

  const detector = useDetectorTiempoReal(videoRef, organo, !errorCamara);

  useEffect(() => {
    let stream: MediaStream | null = null;
    let cancelado = false;
    const video = videoRef.current;

    const iniciar = async () => {
      setErrorCamara(null);
      if (!navigator.mediaDevices?.getUserMedia) {
        setErrorCamara('Tu navegador no permite acceder a la cámara desde esta página.');
        return;
      }
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: camaraActiva,
            // 720p: suficiente para el backend (analiza a 1024 px) y más liviano
            // de decodificar y copiar en cada cuadro que 1080p.
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
          audio: false,
        });
        if (cancelado) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        if (video) {
          video.srcObject = stream;
          await video.play().catch(() => undefined);
        }
      } catch (error) {
        console.error('Error al acceder a la cámara:', error);
        setErrorCamara(
          'No se pudo acceder a la cámara. Verifica que hayas permitido el acceso a la cámara.',
        );
      }
    };

    void iniciar();

    return () => {
      cancelado = true;
      stream?.getTracks().forEach((t) => t.stop());
      if (video) video.srcObject = null;
    };
  }, [camaraActiva]);

  const guardarDiagnostico = () => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return;

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        onGuardar(new File([blob], `tiempo-real-${Date.now()}.jpg`, { type: 'image/jpeg' }));
      },
      'image/jpeg',
      0.92,
    );
  };

  const { detecciones, estado, cargando, error, fps, backend } = detector;
  const enfermedades = Array.from(
    new Set(detecciones.map((d) => d.clase).filter((c) => !esClaseSana(c))),
  );
  const muyLejos =
    detecciones.length > 0 &&
    detecciones.every(
      (d) => (d.caja.x2 - d.caja.x1) * (d.caja.y2 - d.caja.y1) < AREA_MINIMA_OBJETO,
    );

  let mensaje: string;
  if (cargando) mensaje = 'Cargando modelo de detección…';
  else if (error) mensaje = error;
  else if (estado === 'buscando')
    mensaje = `Apunta la cámara a ${organo === 'hoja' ? 'una hoja' : 'un fruto'} de palto`;
  else if (muyLejos) mensaje = 'Acércate más: el objeto se ve muy pequeño';
  else if (estado === 'estabilizando') mensaje = 'Mantén la cámara quieta…';
  else if (enfermedades.length === 0) mensaje = 'Diagnóstico estable: sin enfermedades detectadas';
  else mensaje = `Diagnóstico estable: ${enfermedades.map(formatClase).join(', ')}`;

  const vw = dimVideo?.w ?? 1;
  const vh = dimVideo?.h ?? 1;
  const tamFuente = Math.max(vw, vh) * 0.022;

  return (
    <div className="fixed inset-0 z-[100] bg-black flex flex-col">
      {/* Cabecera */}
      <div className="flex items-center justify-between px-4 py-3 bg-black/80 text-white">
        <div>
          <h2 className="text-base sm:text-lg font-semibold flex items-center gap-2">
            <ScanSearch className="w-5 h-5 text-emerald-400" />
            Diagnóstico en tiempo real
          </h2>
          <p className="text-[11px] text-slate-400">
            {organo === 'hoja' ? 'Modelo de hojas' : 'Modelo de frutos'}
            {backend && ` • ${backend.toUpperCase()} • ${fps.toFixed(1)} FPS`}
          </p>
        </div>
        <button
          type="button"
          onClick={onCerrar}
          className="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
          aria-label="Cerrar cámara"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Vista de cámara + detecciones */}
      <div className="relative flex-1 flex items-center justify-center bg-black overflow-hidden">
        {errorCamara ? (
          <div className="px-6 text-center">
            <Camera className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <p className="text-white text-lg font-semibold mb-2">No se pudo abrir la cámara</p>
            <p className="text-slate-400 text-sm max-w-sm">{errorCamara}</p>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              onLoadedMetadata={(e) =>
                setDimVideo({ w: e.currentTarget.videoWidth, h: e.currentTarget.videoHeight })
              }
              className="w-full h-full object-contain"
            />

            {/* Mismo encuadre que object-contain: viewBox en píxeles del video + "meet". */}
            {dimVideo && (
              <svg
                className="absolute inset-0 w-full h-full pointer-events-none"
                viewBox={`0 0 ${vw} ${vh}`}
                preserveAspectRatio="xMidYMid meet"
              >
                {detecciones.map((det) => {
                  const paleta = paletaDeClase(det.clase);
                  const etiqueta = `${formatClase(det.clase)} ${(det.confianza * 100).toFixed(0)}%`;
                  const altoEtiqueta = tamFuente * 1.5;
                  // Transición CSS: la caja se desliza entre detecciones en vez de saltar.
                  const transicion = 'transform 150ms linear, width 150ms linear, height 150ms linear';
                  return (
                    <g
                      key={det.id}
                      style={{
                        transform: `translate(${det.caja.x1 * vw}px, ${det.caja.y1 * vh}px)`,
                        transition: transicion,
                      }}
                    >
                      <rect
                        style={{
                          width: (det.caja.x2 - det.caja.x1) * vw,
                          height: (det.caja.y2 - det.caja.y1) * vh,
                          transition: transicion,
                        }}
                        fill={paleta.bg}
                        stroke={paleta.stroke}
                        strokeWidth={tamFuente * 0.18}
                        rx={tamFuente * 0.3}
                      />
                      <g
                        transform={
                          det.caja.y1 * vh < altoEtiqueta ? undefined : `translate(0, ${-altoEtiqueta})`
                        }
                      >
                        <rect
                          width={etiqueta.length * tamFuente * 0.6 + tamFuente}
                          height={altoEtiqueta}
                          fill={paleta.stroke}
                          rx={tamFuente * 0.25}
                        />
                        <text
                          x={tamFuente * 0.5}
                          y={tamFuente * 1.1}
                          fill="#ffffff"
                          fontSize={tamFuente}
                          fontWeight="bold"
                          fontFamily="sans-serif"
                        >
                          {etiqueta}
                        </text>
                      </g>
                    </g>
                  );
                })}
              </svg>
            )}

            {/* Estado */}
            <div className="absolute top-3 left-1/2 -translate-x-1/2 max-w-[92%]">
              <div
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium backdrop-blur-md border ${
                  estado === 'estable' && !muyLejos
                    ? 'bg-emerald-500/25 border-emerald-400/60 text-emerald-100'
                    : 'bg-black/60 border-white/15 text-slate-100'
                }`}
              >
                {cargando || estado === 'estabilizando' ? (
                  <Loader2 className="w-4 h-4 animate-spin shrink-0" />
                ) : estado === 'estable' ? (
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-300" />
                ) : (
                  <ScanSearch className="w-4 h-4 shrink-0" />
                )}
                <span className="truncate">{mensaje}</span>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Controles */}
      <div className="bg-black/90 px-6 pt-5 pb-6">
        {errorGuardado && (
          <p className="text-center text-rose-300 text-xs mb-3">{errorGuardado}</p>
        )}
        <div className="flex items-center justify-center gap-6">
          <button
            type="button"
            onClick={() => setCamaraActiva((c) => (c === 'environment' ? 'user' : 'environment'))}
            disabled={!!errorCamara || guardando}
            className="w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 disabled:opacity-40 text-white flex items-center justify-center transition-colors"
            title="Cambiar cámara"
          >
            <RotateCcw className="w-6 h-6" />
          </button>

          <button
            type="button"
            onClick={guardarDiagnostico}
            disabled={!!errorCamara || !dimVideo || guardando}
            className={`inline-flex items-center gap-2 px-6 h-14 rounded-2xl font-semibold whitespace-nowrap transition-all disabled:opacity-40 ${
              estado === 'estable' && !muyLejos
                ? 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-lg shadow-emerald-500/30'
                : 'bg-white/15 hover:bg-white/25 text-white'
            }`}
          >
            {guardando ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Save className="w-5 h-5" />
            )}
            {guardando ? 'Guardando…' : 'Guardar diagnóstico'}
          </button>

          <div className="w-12 h-12" />
        </div>
        <p className="text-center text-slate-400 text-xs mt-4">
          El diagnóstico se actualiza en vivo. Guárdalo cuando aparezca como estable.
        </p>
      </div>
    </div>
  );
};
