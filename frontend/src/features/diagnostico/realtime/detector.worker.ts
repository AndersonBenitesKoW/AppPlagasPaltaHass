/// <reference lib="webworker" />
/**
 * Worker de inferencia: todo el trabajo pesado (escalado, lectura de píxeles,
 * ONNX y NMS) corre aquí para que el hilo principal solo pinte el video.
 */
import * as ort from 'onnxruntime-web/webgpu';
import ortMjsUrl from 'onnxruntime-web/ort-wasm-simd-threaded.asyncify.mjs?url';
import ortWasmUrl from 'onnxruntime-web/ort-wasm-simd-threaded.asyncify.wasm?url';

import type { Deteccion } from '../model/types';
import { postprocesar, preprocesar } from './yolo';

export type BackendInferencia = 'webgpu' | 'wasm';

export interface ConfigModelo {
  archivo: string;
  imgsz: number;
  clases: string[];
}

export type MensajeEntrada =
  | { tipo: 'iniciar'; urlModelo: string; config: ConfigModelo }
  | { tipo: 'detectar'; id: number; cuadro: ImageBitmap };

export type MensajeSalida =
  | { tipo: 'listo'; backend: BackendInferencia }
  | { tipo: 'error'; mensaje: string }
  | { tipo: 'resultado'; id: number; detecciones: Deteccion[] }
  | { tipo: 'fallo'; id: number; mensaje: string };

const ctxWorker = self as unknown as DedicatedWorkerGlobalScope;

let sesion: ort.InferenceSession | null = null;
let config: ConfigModelo | null = null;
let ctx: OffscreenCanvasRenderingContext2D | null = null;
let entrada: Float32Array | null = null;

function responder(m: MensajeSalida): void {
  ctxWorker.postMessage(m);
}

async function crearSesion(url: string): Promise<BackendInferencia> {
  // Rutas explícitas del runtime: sin esto, con multihilo los hilos de WASM
  // intentan arrancar con el script de este worker y la carga se cuelga.
  ort.env.wasm.wasmPaths = { mjs: ortMjsUrl, wasm: ortWasmUrl };
  // Multihilo solo con cross-origin isolation (COOP/COEP); si no, un hilo.
  ort.env.wasm.numThreads = ctxWorker.crossOriginIsolated
    ? Math.min(4, navigator.hardwareConcurrency || 1)
    : 1;

  if ('gpu' in navigator) {
    try {
      sesion = await ort.InferenceSession.create(url, {
        executionProviders: ['webgpu'],
        graphOptimizationLevel: 'all',
      });
      return 'webgpu';
    } catch {
      // WebGPU declarado pero no usable (driver, permisos…): seguimos con WASM.
    }
  }
  sesion = await ort.InferenceSession.create(url, {
    executionProviders: ['wasm'],
    graphOptimizationLevel: 'all',
  });
  return 'wasm';
}

async function detectar(cuadro: ImageBitmap): Promise<Deteccion[]> {
  if (!sesion || !config || !ctx || !entrada) throw new Error('Modelo no iniciado');
  const lado = config.imgsz;
  const lb = preprocesar(ctx, cuadro, lado, entrada);
  const tensor = new ort.Tensor('float32', entrada, [1, 3, lado, lado]);
  const salidas = await sesion.run({ [sesion.inputNames[0]]: tensor });
  const salida = salidas[sesion.outputNames[0]];
  const detecciones = postprocesar(salida.data as Float32Array, salida.dims[2], config.clases, lb);
  salida.dispose();
  return detecciones;
}

ctxWorker.onmessage = async (ev: MessageEvent<MensajeEntrada>) => {
  const m = ev.data;

  if (m.tipo === 'iniciar') {
    try {
      config = m.config;
      const lienzo = new OffscreenCanvas(config.imgsz, config.imgsz);
      ctx = lienzo.getContext('2d', { willReadFrequently: true });
      if (!ctx) throw new Error('OffscreenCanvas 2D no disponible');
      entrada = new Float32Array(3 * config.imgsz * config.imgsz);
      const backend = await crearSesion(m.urlModelo);
      responder({ tipo: 'listo', backend });
    } catch (e) {
      responder({ tipo: 'error', mensaje: e instanceof Error ? e.message : String(e) });
    }
    return;
  }

  if (m.tipo === 'detectar') {
    try {
      const detecciones = await detectar(m.cuadro);
      responder({ tipo: 'resultado', id: m.id, detecciones });
    } catch (e) {
      responder({ tipo: 'fallo', id: m.id, mensaje: e instanceof Error ? e.message : String(e) });
    } finally {
      m.cuadro.close();
    }
  }
};
