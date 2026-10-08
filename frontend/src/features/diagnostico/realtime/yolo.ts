import type { Deteccion } from '../model/types';

/** Funciones puras de pre/post-procesamiento YOLO11 (usadas dentro del worker). */

export const CONF_MINIMA = 0.35; // igual que APP_UMBRAL_CONFIANZA del backend
const IOU_NMS = 0.45;
const MAX_DETECCIONES = 50;
const RELLENO_LETTERBOX = 114;

export interface Letterbox {
  escala: number;
  padX: number;
  padY: number;
  anchoFuente: number;
  altoFuente: number;
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

/**
 * Letterbox igual que Ultralytics (reescalado sin deformar + relleno gris) y
 * conversión a tensor CHW normalizado 0..1 dentro de `entrada`.
 */
export function preprocesar(
  ctx: OffscreenCanvasRenderingContext2D,
  fuente: ImageBitmap,
  lado: number,
  entrada: Float32Array,
): Letterbox {
  const anchoFuente = fuente.width;
  const altoFuente = fuente.height;
  const escala = Math.min(lado / anchoFuente, lado / altoFuente);
  const ancho = Math.round(anchoFuente * escala);
  const alto = Math.round(altoFuente * escala);
  const padX = (lado - ancho) / 2;
  const padY = (lado - alto) / 2;

  ctx.fillStyle = `rgb(${RELLENO_LETTERBOX},${RELLENO_LETTERBOX},${RELLENO_LETTERBOX})`;
  ctx.fillRect(0, 0, lado, lado);
  ctx.drawImage(fuente, padX, padY, ancho, alto);
  const pixeles = ctx.getImageData(0, 0, lado, lado).data;

  const area = lado * lado;
  for (let i = 0, p = 0; i < area; i++, p += 4) {
    entrada[i] = pixeles[p] / 255;
    entrada[area + i] = pixeles[p + 1] / 255;
    entrada[2 * area + i] = pixeles[p + 2] / 255;
  }
  return { escala, padX, padY, anchoFuente, altoFuente };
}

/**
 * Salida YOLO11: [1, 4 + clases, n] con (cx, cy, w, h) en píxeles del letterbox.
 * Devuelve cajas normalizadas (0..1) respecto a la imagen fuente, tras NMS por clase.
 */
export function postprocesar(
  datos: Float32Array,
  n: number,
  clases: string[],
  lb: Letterbox,
): Deteccion[] {
  const numClases = clases.length;
  const limitar = (v: number) => Math.max(0, Math.min(1, v));
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
    candidatas.push({
      clase: clases[claseIdx],
      confianza: mejor,
      caja: {
        x1: limitar((cx - w / 2 - lb.padX) / lb.escala / lb.anchoFuente),
        y1: limitar((cy - h / 2 - lb.padY) / lb.escala / lb.altoFuente),
        x2: limitar((cx + w / 2 - lb.padX) / lb.escala / lb.anchoFuente),
        y2: limitar((cy + h / 2 - lb.padY) / lb.escala / lb.altoFuente),
      },
    });
  }

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
