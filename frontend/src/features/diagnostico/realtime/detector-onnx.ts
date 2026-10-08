import type * as Ort from 'onnxruntime-web';
import type { Organo } from '../api/diagnostico.api';
import type { Deteccion } from '../model/types';

type OrtModule = typeof Ort;
export type BackendInferencia = 'webgpu' | 'wasm';

interface ConfigModelo {
  archivo: string;
  imgsz: number;
  clases: string[];
}

const BASE_MODELOS = `${import.meta.env.BASE_URL}modelos/`;
const CONF_MINIMA = 0.35; // igual que APP_UMBRAL_CONFIANZA del backend
const IOU_NMS = 0.45;
const MAX_DETECCIONES = 50;
const RELLENO_LETTERBOX = 114;

// onnxruntime-web pesa varios MB: se carga solo al abrir la cámara.
let ortPromise: Promise<OrtModule> | null = null;
function cargarOrt(): Promise<OrtModule> {
  ortPromise ??= import('onnxruntime-web/webgpu');
  return ortPromise;
}

let manifiestoPromise: Promise<Record<Organo, ConfigModelo>> | null = null;
function cargarManifiesto(): Promise<Record<Organo, ConfigModelo>> {
  manifiestoPromise ??= fetch(`${BASE_MODELOS}modelos.json`).then((r) => {
    if (!r.ok) throw new Error('No se encontró la configuración de los modelos.');
    return r.json() as Promise<Record<Organo, ConfigModelo>>;
  });
  return manifiestoPromise;
}

export function iou(a: Deteccion['caja'], b: Deteccion['caja']): number {
  const x1 = Math.max(a.x1, b.x1);
  const y1 = Math.max(a.y1, b.y1);
  const x2 = Math.min(a.x2, b.x2);
  const y2 = Math.min(a.y2, b.y2);
  const interseccion = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
  const union =
    (a.x2 - a.x1) * (a.y2 - a.y1) + (b.x2 - b.x1) * (b.y2 - b.y1) - interseccion;
  return union > 0 ? interseccion / union : 0;
}

/** Detector YOLO11 que corre en el navegador (WebGPU si está disponible, si no WASM). */
export class DetectorOnnx {
  private readonly lienzo: HTMLCanvasElement;
  private readonly ctx: CanvasRenderingContext2D;
  private readonly entrada: Float32Array;

  private constructor(
    private readonly ort: OrtModule,
    private readonly sesion: Ort.InferenceSession,
    private readonly config: ConfigModelo,
    readonly backend: BackendInferencia,
  ) {
    const lado = config.imgsz;
    this.lienzo = document.createElement('canvas');
    this.lienzo.width = lado;
    this.lienzo.height = lado;
    const ctx = this.lienzo.getContext('2d', { willReadFrequently: true });
    if (!ctx) throw new Error('El navegador no soporta canvas 2D.');
    this.ctx = ctx;
    this.entrada = new Float32Array(3 * lado * lado);
  }

  static async crear(organo: Organo): Promise<DetectorOnnx> {
    const [ort, manifiesto] = await Promise.all([cargarOrt(), cargarManifiesto()]);
    const config = manifiesto[organo];
    if (!config) throw new Error(`No hay modelo en tiempo real para "${organo}".`);

    // Multihilo solo con cross-origin isolation; sin ella WASM exige un hilo.
    ort.env.wasm.numThreads = globalThis.crossOriginIsolated
      ? Math.min(4, navigator.hardwareConcurrency || 1)
      : 1;

    const url = `${BASE_MODELOS}${config.archivo}`;
    if ('gpu' in navigator) {
      try {
        const sesion = await ort.InferenceSession.create(url, {
          executionProviders: ['webgpu'],
          graphOptimizationLevel: 'all',
        });
        return new DetectorOnnx(ort, sesion, config, 'webgpu');
      } catch {
        // WebGPU declarado pero no usable (driver, permisos…): seguimos con WASM.
      }
    }
    const sesion = await ort.InferenceSession.create(url, {
      executionProviders: ['wasm'],
      graphOptimizationLevel: 'all',
    });
    return new DetectorOnnx(ort, sesion, config, 'wasm');
  }

  /** Detecta sobre el cuadro actual. Las cajas salen normalizadas (0..1) respecto a la fuente. */
  async detectar(fuente: HTMLVideoElement): Promise<Deteccion[]> {
    const anchoFuente = fuente.videoWidth;
    const altoFuente = fuente.videoHeight;
    if (!anchoFuente || !altoFuente) return [];

    const lado = this.config.imgsz;
    const escala = Math.min(lado / anchoFuente, lado / altoFuente);
    const ancho = Math.round(anchoFuente * escala);
    const alto = Math.round(altoFuente * escala);
    const padX = (lado - ancho) / 2;
    const padY = (lado - alto) / 2;

    // Letterbox igual que Ultralytics: reescalado sin deformar + relleno gris.
    this.ctx.fillStyle = `rgb(${RELLENO_LETTERBOX},${RELLENO_LETTERBOX},${RELLENO_LETTERBOX})`;
    this.ctx.fillRect(0, 0, lado, lado);
    this.ctx.drawImage(fuente, padX, padY, ancho, alto);
    const pixeles = this.ctx.getImageData(0, 0, lado, lado).data;

    const area = lado * lado;
    for (let i = 0; i < area; i++) {
      this.entrada[i] = pixeles[i * 4] / 255;
      this.entrada[area + i] = pixeles[i * 4 + 1] / 255;
      this.entrada[2 * area + i] = pixeles[i * 4 + 2] / 255;
    }

    const tensor = new this.ort.Tensor('float32', this.entrada, [1, 3, lado, lado]);
    const salidas = await this.sesion.run({ [this.sesion.inputNames[0]]: tensor });
    const salida = salidas[this.sesion.outputNames[0]];
    const datos = salida.data as Float32Array;
    const n = salida.dims[2];
    const numClases = this.config.clases.length;

    // Salida YOLO11: [1, 4 + clases, n] con (cx, cy, w, h) en píxeles del letterbox.
    const candidatas: Deteccion[] = [];
    for (let i = 0; i < n; i++) {
      let mejor = 0;
      let claseIdx = -1;
      for (let c = 0; c < numClases; c++) {
        const p = datos[(4 + c) * n + i];
        if (p > mejor) {
          mejor = p;
          claseIdx = c;
        }
      }
      if (mejor < CONF_MINIMA) continue;

      const cx = datos[i];
      const cy = datos[n + i];
      const w = datos[2 * n + i];
      const h = datos[3 * n + i];
      const limitar = (v: number) => Math.max(0, Math.min(1, v));
      candidatas.push({
        clase: this.config.clases[claseIdx],
        confianza: mejor,
        caja: {
          x1: limitar((cx - w / 2 - padX) / escala / anchoFuente),
          y1: limitar((cy - h / 2 - padY) / escala / altoFuente),
          x2: limitar((cx + w / 2 - padX) / escala / anchoFuente),
          y2: limitar((cy + h / 2 - padY) / escala / altoFuente),
        },
      });
    }

    // NMS por clase.
    candidatas.sort((a, b) => b.confianza - a.confianza);
    const resultado: Deteccion[] = [];
    for (const det of candidatas) {
      const solapada = resultado.some(
        (r) => r.clase === det.clase && iou(r.caja, det.caja) > IOU_NMS,
      );
      if (!solapada) resultado.push(det);
      if (resultado.length >= MAX_DETECCIONES) break;
    }
    return resultado;
  }

  liberar(): void {
    void this.sesion.release();
  }
}
