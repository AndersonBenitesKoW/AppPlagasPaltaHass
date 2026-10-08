import type { Deteccion } from '../model/types';
import { iou } from './detector-onnx';

/** Parámetros de estabilidad. Más cuadros = más estable pero más lento en reaccionar. */
const IOU_ASOCIACION = 0.3; // solape mínimo para considerar que es el mismo objeto
const SUAVIZADO_CAJA = 0.4; // peso del cuadro nuevo en la posición de la caja
const DECAIMIENTO_VOTOS = 0.85; // cuánto "olvida" la clase en cada cuadro
const MIN_ACIERTOS_VISIBLE = 3; // cuadros seguidos para mostrar un objeto
const MIN_ACIERTOS_ESTABLE = 8; // cuadros seguidos para declarar el diagnóstico estable
const MAX_FALLOS = 4; // cuadros sin verlo antes de olvidarlo (evita parpadeo)

interface Pista {
  caja: Deteccion['caja'];
  votos: Map<string, number>;
  confianza: number;
  aciertos: number;
  fallos: number;
  claseAnterior: string;
}

export type EstadoEstabilidad = 'buscando' | 'estabilizando' | 'estable';

export interface ResultadoEstable {
  detecciones: Deteccion[];
  estado: EstadoEstabilidad;
}

function claseGanadora(votos: Map<string, number>): string {
  let mejor = '';
  let max = -1;
  for (const [clase, v] of votos) {
    if (v > max) {
      max = v;
      mejor = clase;
    }
  }
  return mejor;
}

function mezclar(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/**
 * Estabiliza las detecciones cuadro a cuadro:
 * - asocia cada detección con el objeto que ya se seguía (por solape),
 * - suaviza la caja para que no tiemble,
 * - decide la clase por votación acumulada, para que no salte entre enfermedades,
 * - solo muestra objetos vistos varios cuadros seguidos.
 */
export class Estabilizador {
  private pistas: Pista[] = [];

  reiniciar(): void {
    this.pistas = [];
  }

  actualizar(detecciones: Deteccion[]): ResultadoEstable {
    const libres = new Set(this.pistas.map((_, i) => i));
    const asignadas = new Set<number>();

    // Asociación codiciosa por mayor IoU, sin importar la clase (la clase la decide el voto).
    const pares: { pista: number; det: number; valor: number }[] = [];
    this.pistas.forEach((p, i) =>
      detecciones.forEach((d, j) => {
        const valor = iou(p.caja, d.caja);
        if (valor >= IOU_ASOCIACION) pares.push({ pista: i, det: j, valor });
      }),
    );
    pares.sort((a, b) => b.valor - a.valor);

    for (const { pista, det } of pares) {
      if (!libres.has(pista) || asignadas.has(det)) continue;
      libres.delete(pista);
      asignadas.add(det);

      const p = this.pistas[pista];
      const d = detecciones[det];
      p.caja = {
        x1: mezclar(p.caja.x1, d.caja.x1, SUAVIZADO_CAJA),
        y1: mezclar(p.caja.y1, d.caja.y1, SUAVIZADO_CAJA),
        x2: mezclar(p.caja.x2, d.caja.x2, SUAVIZADO_CAJA),
        y2: mezclar(p.caja.y2, d.caja.y2, SUAVIZADO_CAJA),
      };
      for (const [clase, v] of p.votos) p.votos.set(clase, v * DECAIMIENTO_VOTOS);
      p.votos.set(d.clase, (p.votos.get(d.clase) ?? 0) + d.confianza);
      p.confianza = mezclar(p.confianza, d.confianza, 0.3);
      p.aciertos += 1;
      p.fallos = 0;
    }

    for (const i of libres) this.pistas[i].fallos += 1;
    this.pistas = this.pistas.filter((p) => p.fallos <= MAX_FALLOS);

    detecciones.forEach((d, j) => {
      if (asignadas.has(j)) return;
      this.pistas.push({
        caja: { ...d.caja },
        votos: new Map([[d.clase, d.confianza]]),
        confianza: d.confianza,
        aciertos: 1,
        fallos: 0,
        claseAnterior: d.clase,
      });
    });

    const visibles = this.pistas.filter((p) => p.aciertos >= MIN_ACIERTOS_VISIBLE);
    let estable = visibles.length > 0;
    const salida: Deteccion[] = visibles.map((p) => {
      const clase = claseGanadora(p.votos);
      if (clase !== p.claseAnterior) {
        // Cambió la clase ganadora: se exige volver a acumular confirmaciones.
        p.claseAnterior = clase;
        p.aciertos = MIN_ACIERTOS_VISIBLE;
      }
      if (p.aciertos < MIN_ACIERTOS_ESTABLE) estable = false;
      return { clase, confianza: p.confianza, caja: { ...p.caja } };
    });

    return {
      detecciones: salida,
      estado: visibles.length === 0 ? 'buscando' : estable ? 'estable' : 'estabilizando',
    };
  }
}
