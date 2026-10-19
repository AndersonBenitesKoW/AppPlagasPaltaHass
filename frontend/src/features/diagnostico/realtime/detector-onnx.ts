import type { Organo } from '../api/diagnostico.api';
import type { Deteccion } from '../model/types';
import type {
  BackendInferencia,
  ConfigModelo,
  MensajeEntrada,
  MensajeSalida,
} from './detector.worker';

export type { BackendInferencia };

const BASE_MODELOS = `${import.meta.env.BASE_URL}modelos/`;

let manifiestoPromise: Promise<Record<Organo, ConfigModelo>> | null = null;
function cargarManifiesto(): Promise<Record<Organo, ConfigModelo>> {
  manifiestoPromise ??= fetch(`${BASE_MODELOS}modelos.json`).then((r) => {
    if (!r.ok) throw new Error('No se encontró la configuración de los modelos.');
    return r.json() as Promise<Record<Organo, ConfigModelo>>;
  });
  return manifiestoPromise;
}

/**
 * Detector YOLO11 en el navegador. La inferencia corre en un Web Worker
 * (WebGPU si está disponible, si no WASM); aquí solo se captura el cuadro.
 */
export class DetectorOnnx {
  private siguienteId = 0;
  private readonly pendientes = new Map<
    number,
    { resolver: (d: Deteccion[]) => void; rechazar: (e: Error) => void }
  >();

  private constructor(
    private readonly worker: Worker,
    private readonly imgsz: number,
    readonly backend: BackendInferencia,
  ) {
    worker.onmessage = (ev: MessageEvent<MensajeSalida>) => {
      const m = ev.data;
      if (m.tipo !== 'resultado' && m.tipo !== 'fallo') return;
      const p = this.pendientes.get(m.id);
      if (!p) return;
      this.pendientes.delete(m.id);
      if (m.tipo === 'resultado') p.resolver(m.detecciones);
      else p.rechazar(new Error(m.mensaje));
    };
  }

  static async crear(organo: Organo): Promise<DetectorOnnx> {
    const manifiesto = await cargarManifiesto();
    const config = manifiesto[organo];
    if (!config) throw new Error(`No hay modelo en tiempo real para "${organo}".`);

    const worker = new Worker(new URL('./detector.worker.ts', import.meta.url), {
      type: 'module',
    });
    const urlModelo = new URL(`${BASE_MODELOS}${config.archivo}`, location.href).href;

    try {
      const backend = await new Promise<BackendInferencia>((resolver, rechazar) => {
        worker.onmessage = (ev: MessageEvent<MensajeSalida>) => {
          if (ev.data.tipo === 'listo') resolver(ev.data.backend);
          else if (ev.data.tipo === 'error') rechazar(new Error(ev.data.mensaje));
        };
        worker.onerror = (ev) => rechazar(new Error(ev.message || 'Error en el worker'));
        const m: MensajeEntrada = { tipo: 'iniciar', urlModelo, config };
        worker.postMessage(m);
      });
      worker.onerror = null;
      return new DetectorOnnx(worker, config.imgsz, backend);
    } catch (e) {
      worker.terminate();
      throw e;
    }
  }

  /** Detecta sobre el cuadro actual. Las cajas salen normalizadas (0..1) respecto al video. */
  async detectar(video: HTMLVideoElement): Promise<Deteccion[]> {
    const { videoWidth: w, videoHeight: h } = video;
    if (!w || !h) return [];

    // Reducir al tamaño de entrada al crear el bitmap: menos memoria y menos
    // trabajo en el worker. Mantiene la proporción, así las cajas siguen valiendo.
    const escala = Math.min(1, this.imgsz / Math.max(w, h));
    let cuadro: ImageBitmap;
    try {
      cuadro = await createImageBitmap(video, {
        resizeWidth: Math.round(w * escala),
        resizeHeight: Math.round(h * escala),
        resizeQuality: 'medium',
      });
    } catch {
      cuadro = await createImageBitmap(video);
    }

    const id = this.siguienteId++;
    return new Promise<Deteccion[]>((resolver, rechazar) => {
      this.pendientes.set(id, { resolver, rechazar });
      const m: MensajeEntrada = { tipo: 'detectar', id, cuadro };
      this.worker.postMessage(m, [cuadro]);
    });
  }

  liberar(): void {
    this.worker.terminate();
    for (const p of this.pendientes.values()) p.rechazar(new Error('Detector liberado'));
    this.pendientes.clear();
  }
}
