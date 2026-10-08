import { useEffect, useRef, useState, type RefObject } from 'react';

import type { Organo } from '../api/diagnostico.api';
import type { Deteccion } from '../model/types';
import { DetectorOnnx, type BackendInferencia } from '../realtime/detector-onnx';
import { Estabilizador, type EstadoEstabilidad } from '../realtime/estabilizador';

export interface EstadoDetectorTiempoReal {
  cargando: boolean;
  error: string | null;
  backend: BackendInferencia | null;
  fps: number;
  detecciones: Deteccion[];
  estado: EstadoEstabilidad;
}

const INICIAL: EstadoDetectorTiempoReal = {
  cargando: true,
  error: null,
  backend: null,
  fps: 0,
  detecciones: [],
  estado: 'buscando',
};

/**
 * Corre el modelo ONNX sobre el video de forma continua (un cuadro a la vez:
 * cuando termina una inferencia empieza la siguiente) y estabiliza el resultado.
 */
export function useDetectorTiempoReal(
  videoRef: RefObject<HTMLVideoElement | null>,
  organo: Organo,
  activo: boolean,
): EstadoDetectorTiempoReal {
  const [estado, setEstado] = useState<EstadoDetectorTiempoReal>(INICIAL);
  const estabilizadorRef = useRef(new Estabilizador());

  useEffect(() => {
    if (!activo) return;

    let cancelado = false;
    let detector: DetectorOnnx | null = null;
    let frameId = 0;
    let enCurso: Promise<unknown> = Promise.resolve();
    const estabilizador = estabilizadorRef.current;
    estabilizador.reiniciar();
    setEstado(INICIAL);

    const bucle = async () => {
      if (cancelado || !detector) return;
      const video = videoRef.current;

      if (video && video.readyState >= 2 && !video.paused) {
        const inicio = performance.now();
        try {
          const inferencia = detector.detectar(video);
          enCurso = inferencia.catch(() => undefined);
          const crudas = await inferencia;
          if (cancelado) return;
          const { detecciones, estado: estabilidad } = estabilizador.actualizar(crudas);
          const instantaneo = 1000 / Math.max(1, performance.now() - inicio);
          setEstado((prev) => ({
            ...prev,
            detecciones,
            estado: estabilidad,
            fps: prev.fps ? prev.fps * 0.8 + instantaneo * 0.2 : instantaneo,
          }));
        } catch (e) {
          if (cancelado) return;
          console.error('Error en la inferencia en tiempo real:', e);
        }
      }
      if (!cancelado) frameId = requestAnimationFrame(() => void bucle());
    };

    DetectorOnnx.crear(organo)
      .then((d) => {
        if (cancelado) {
          d.liberar();
          return;
        }
        detector = d;
        setEstado((prev) => ({ ...prev, cargando: false, backend: d.backend }));
        void bucle();
      })
      .catch((e: unknown) => {
        console.error('No se pudo cargar el modelo en tiempo real:', e);
        if (!cancelado) {
          setEstado((prev) => ({
            ...prev,
            cargando: false,
            error: 'No se pudo cargar el modelo de detección en este dispositivo.',
          }));
        }
      });

    return () => {
      cancelado = true;
      cancelAnimationFrame(frameId);
      // Liberar la sesión solo cuando termine la inferencia en curso.
      const d = detector;
      void enCurso.finally(() => d?.liberar());
    };
  }, [videoRef, organo, activo]);

  return estado;
}
