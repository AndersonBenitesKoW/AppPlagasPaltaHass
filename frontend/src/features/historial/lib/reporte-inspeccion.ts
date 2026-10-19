import type { Diagnostico } from '../../../shared/types/diagnostico';
import { getApiUrl } from '../../../core/config/api-url';

/**
 * Genera un reporte de inspección autocontenido (HTML con las imágenes embebidas y las
 * cajas de detección dibujadas) y lo descarga. El archivo se abre en cualquier navegador
 * y trae un botón para imprimirlo o guardarlo como PDF.
 */

const NOMBRES: Record<string, string> = {
  hoja_sana: 'Hoja Sana',
  antracnosis_hoja: 'Antracnosis en Hoja (Colletotrichum)',
  plaga: 'Afección por Plagas (Trips / Ácaros)',
  deficiencia_nutricional: 'Deficiencia Nutricional (Clorosis)',
  fruto_sano: 'Fruto Sano',
  antracnosis_fruto: 'Antracnosis en Fruto',
  cercospora: 'Cercospora',
  rona: 'Roña',
  pudricion_peduncular: 'Pudrición Peduncular',
  sunblotch: 'Sunblotch',
};

const COLORES: Record<string, string> = {
  hoja_sana: '#10b981',
  fruto_sano: '#10b981',
  antracnosis_hoja: '#f43f5e',
  antracnosis_fruto: '#f43f5e',
  plaga: '#f59e0b',
  deficiencia_nutricional: '#a855f7',
  cercospora: '#f97316',
  rona: '#eab308',
  pudricion_peduncular: '#a855f7',
  sunblotch: '#ec4899',
};

const RECOMENDACION_POR_DEFECTO =
  'Mantener el programa habitual de riego y fertilización. Monitorear periódicamente el dosel del árbol para detectar oportunamente cualquier cambio.';

function nombreClase(clase: string): string {
  return NOMBRES[clase] ?? clase.replace(/_/g, ' ');
}

function escapar(texto: string): string {
  return texto
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString('es-PE', { dateStyle: 'long', timeStyle: 'short' });
}

function cargarImagen(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`No se pudo cargar la imagen ${src}`));
    img.src = src;
  });
}

/** Descarga la imagen y la devuelve como data URL JPEG con las cajas dibujadas encima. */
async function imagenAnotada(diag: Diagnostico): Promise<string | null> {
  try {
    const respuesta = await fetch(getApiUrl(diag.imagen_url));
    if (!respuesta.ok) return null;
    const urlObjeto = URL.createObjectURL(await respuesta.blob());
    try {
      const img = await cargarImagen(urlObjeto);
      const escala = Math.min(1, 1280 / Math.max(img.naturalWidth, img.naturalHeight));
      const ancho = Math.round(img.naturalWidth * escala);
      const alto = Math.round(img.naturalHeight * escala);

      const canvas = document.createElement('canvas');
      canvas.width = ancho;
      canvas.height = alto;
      const ctx = canvas.getContext('2d');
      if (!ctx) return null;
      ctx.drawImage(img, 0, 0, ancho, alto);

      const grosor = Math.max(2, Math.round(ancho / 300));
      const fuente = Math.max(12, Math.round(ancho / 45));
      ctx.font = `bold ${fuente}px sans-serif`;
      ctx.textBaseline = 'top';

      for (const det of diag.detecciones) {
        const color = COLORES[det.clase] ?? '#38bdf8';
        const x = det.caja.x1 * ancho;
        const y = det.caja.y1 * alto;
        const w = (det.caja.x2 - det.caja.x1) * ancho;
        const h = (det.caja.y2 - det.caja.y1) * alto;

        ctx.strokeStyle = color;
        ctx.lineWidth = grosor;
        ctx.strokeRect(x, y, w, h);

        const etiqueta = `${nombreClase(det.clase)} ${(det.confianza * 100).toFixed(0)}%`;
        const anchoTexto = ctx.measureText(etiqueta).width + 8;
        const yEtiqueta = y - fuente - 6 >= 0 ? y - fuente - 6 : y;
        ctx.fillStyle = color;
        ctx.fillRect(x, yEtiqueta, anchoTexto, fuente + 6);
        ctx.fillStyle = '#ffffff';
        ctx.fillText(etiqueta, x + 4, yEtiqueta + 3);
      }

      return canvas.toDataURL('image/jpeg', 0.85);
    } finally {
      URL.revokeObjectURL(urlObjeto);
    }
  } catch {
    return null;
  }
}

function seccionDiagnostico(diag: Diagnostico, imagen: string | null, indice: number): string {
  const organo = diag.organo === 'fruto' ? 'Fruto' : 'Hoja';
  const veredicto = diag.es_sano
    ? `${organo} en estado saludable`
    : 'Alerta fitosanitaria detectada';

  const enfermedades =
    diag.enfermedades.length === 0
      ? '<span class="chip sano">Sin enfermedades</span>'
      : diag.enfermedades
          .map(
            (e) =>
              `<span class="chip" style="border-color:${COLORES[e] ?? '#38bdf8'};color:${COLORES[e] ?? '#38bdf8'}">${escapar(nombreClase(e))}</span>`,
          )
          .join(' ');

  const filas =
    diag.detecciones.length === 0
      ? '<tr><td colspan="3" class="vacio">Sin detecciones</td></tr>'
      : diag.detecciones
          .map(
            (d, i) =>
              `<tr><td>${i + 1}</td><td>${escapar(nombreClase(d.clase))}</td><td>${(d.confianza * 100).toFixed(1)}%</td></tr>`,
          )
          .join('');

  const recomendaciones = diag.conclusiones?.recomendaciones_agronomicas?.length
    ? diag.conclusiones.recomendaciones_agronomicas
    : [RECOMENDACION_POR_DEFECTO];

  return `
  <section class="registro">
    <header>
      <h2>Inspección #${indice} — ${organo}</h2>
      <span class="estado ${diag.es_sano ? 'sano' : 'alerta'}">${diag.es_sano ? 'SANO' : 'ALERTA'}</span>
    </header>
    <div class="cuerpo">
      <div class="imagen">
        ${imagen ? `<img src="${imagen}" alt="Muestra ${indice}">` : '<div class="sin-imagen">Imagen no disponible</div>'}
      </div>
      <div class="datos">
        <dl>
          <dt>Fecha</dt><dd>${escapar(formatearFecha(diag.creado_en))}</dd>
          <dt>ID</dt><dd class="mono">${escapar(diag.id)}</dd>
          <dt>Órgano</dt><dd>${organo}</dd>
          <dt>Veredicto</dt><dd><strong>${veredicto}</strong></dd>
        </dl>
        <h3>Enfermedades</h3>
        <div>${enfermedades}</div>
        <h3>Detecciones (${diag.detecciones.length})</h3>
        <table>
          <thead><tr><th>#</th><th>Clase</th><th>Confianza</th></tr></thead>
          <tbody>${filas}</tbody>
        </table>
        <h3>Acciones recomendadas</h3>
        <ul>${recomendaciones.map((r) => `<li>${escapar(r)}</li>`).join('')}</ul>
      </div>
    </div>
  </section>`;
}

function documentoHtml(diagnosticos: Diagnostico[], imagenes: (string | null)[]): string {
  const total = diagnosticos.length;
  const enfermos = diagnosticos.filter((d) => !d.es_sano).length;
  const generado = new Date().toLocaleString('es-PE', { dateStyle: 'long', timeStyle: 'short' });

  const conteo = new Map<string, number>();
  for (const d of diagnosticos) {
    for (const e of d.enfermedades) conteo.set(e, (conteo.get(e) ?? 0) + 1);
  }
  const resumenEnfermedades =
    conteo.size === 0
      ? ''
      : `<p class="resumen-enf">${[...conteo.entries()]
          .map(([e, n]) => `${escapar(nombreClase(e))}: <strong>${n}</strong>`)
          .join(' · ')}</p>`;

  return `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reporte de Inspección — PaltaVision</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; color: #1e293b; background: #f1f5f9; margin: 0; padding: 24px; }
  .contenedor { max-width: 1000px; margin: 0 auto; }
  .portada { background: #064e3b; color: #ecfdf5; padding: 24px 28px; border-radius: 14px; margin-bottom: 20px; }
  .portada h1 { margin: 0 0 4px; font-size: 24px; }
  .portada p { margin: 2px 0; font-size: 13px; opacity: .85; }
  .kpis { display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; }
  .kpi { background: rgba(255,255,255,.1); border-radius: 10px; padding: 10px 16px; min-width: 120px; }
  .kpi b { display: block; font-size: 22px; }
  .resumen-enf { font-size: 13px; margin-top: 12px !important; }
  .acciones { text-align: right; margin-bottom: 16px; }
  .acciones button { background: #059669; color: #fff; border: 0; padding: 10px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; }
  .registro { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px 20px; margin-bottom: 18px; page-break-inside: avoid; break-inside: avoid; }
  .registro header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 14px; }
  .registro h2 { font-size: 17px; margin: 0; }
  .estado { font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 999px; color: #fff; }
  .estado.sano { background: #059669; } .estado.alerta { background: #e11d48; }
  .cuerpo { display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px; }
  .imagen img { width: 100%; border-radius: 10px; border: 1px solid #e2e8f0; }
  .sin-imagen { aspect-ratio: 4/3; display: flex; align-items: center; justify-content: center; background: #f1f5f9; border-radius: 10px; color: #64748b; font-size: 13px; }
  dl { display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; font-size: 13px; margin: 0 0 8px; }
  dt { color: #64748b; } dd { margin: 0; }
  .mono { font-family: ui-monospace, monospace; font-size: 11px; word-break: break-all; }
  h3 { font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: #64748b; margin: 14px 0 6px; }
  .chip { display: inline-block; border: 1.5px solid; border-radius: 999px; padding: 2px 10px; font-size: 12px; font-weight: 600; margin: 0 4px 4px 0; }
  .chip.sano { border-color: #059669; color: #059669; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th, td { text-align: left; padding: 5px 6px; border-bottom: 1px solid #f1f5f9; }
  th { color: #64748b; font-weight: 600; }
  .vacio { color: #94a3b8; }
  ul { margin: 0; padding-left: 18px; font-size: 12.5px; line-height: 1.5; }
  footer.pie { text-align: center; font-size: 11px; color: #94a3b8; margin-top: 24px; }
  @media (max-width: 700px) { .cuerpo { grid-template-columns: 1fr; } body { padding: 12px; } }
  @media print {
    body { background: #fff; padding: 0; }
    .acciones { display: none; }
    .portada { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .estado, .chip { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
</style>
</head>
<body>
<div class="contenedor">
  <div class="acciones"><button onclick="window.print()">Imprimir / Guardar como PDF</button></div>
  <div class="portada">
    <h1>Reporte de Inspección Fitosanitaria — Palta Hass</h1>
    <p>Generado el ${escapar(generado)} · PaltaVision (YOLO11)</p>
    <div class="kpis">
      <div class="kpi"><b>${total}</b>Inspecciones</div>
      <div class="kpi"><b>${enfermos}</b>Con alerta</div>
      <div class="kpi"><b>${total - enfermos}</b>Sanas</div>
    </div>
    ${resumenEnfermedades}
  </div>
  ${diagnosticos.map((d, i) => seccionDiagnostico(d, imagenes[i], i + 1)).join('')}
  <footer class="pie">© ${new Date().getFullYear()} PaltaVision · Reporte generado automáticamente</footer>
</div>
</body>
</html>`;
}

function descargar(contenido: string, nombreArchivo: string): void {
  const blob = new Blob([contenido], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombreArchivo;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function exportarReporteInspeccion(diagnosticos: Diagnostico[]): Promise<void> {
  if (diagnosticos.length === 0) return;

  const imagenes = await Promise.all(diagnosticos.map(imagenAnotada));
  const html = documentoHtml(diagnosticos, imagenes);

  const fecha = new Date().toISOString().slice(0, 10);
  const nombre =
    diagnosticos.length === 1
      ? `inspeccion-${diagnosticos[0].id.slice(0, 8)}-${fecha}.html`
      : `historial-inspecciones-${fecha}.html`;

  descargar(html, nombre);
}
