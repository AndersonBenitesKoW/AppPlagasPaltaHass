# Pendientes de la tesis

Documentos de trabajo (el original no se modificó):
- `... - v2 Cap I corregido.docx`: correcciones del Cap. I con control de cambios.
- `... - v3 Cap III resultados.docx`: el v2 más el Cap. III de resultados. Al abrirlo, presionar Ctrl+A y luego F9 para actualizar la numeración y los índices.

Las métricas, las figuras y los scripts de evaluación están en `resultados-cap3/`.

---

## 1. Citas sin fuente (subsanar o reemplazar)

No figuran en Referencias, no hay PDF en `pdfs/` y ya venían así desde `Tesis_Inicial.docx`. Cada una tiene un comentario en el Word.

| Cita | Dónde aparece | Problema | Opciones |
|---|---|---|---|
| **Mendoza (2012)** | Cap. I › Bases teóricas › proceso de inspección y control en campo | La definición ("función administrativa que consiste en medir, registrar y revisar el desempeño… para asegurar que se ajuste a los planes") corresponde al concepto de *control* en administración, no a una fuente agrícola | a) Conseguir la referencia completa (autor, título, editorial/revista, DOI o URL) y agregarla. b) Reemplazar la fuente por Campos Paredes (2025), que trata el monitoreo fitosanitario en Chao (ya está en Referencias) |
| **Rodríguez et al. (2018)** | Cap. I › Bases teóricas › tiempo de detección | No se identificó la fuente | a) Agregar la referencia completa. b) Sustentar con Bompani et al. (2024), que miden el tiempo de inferencia (147 ms por imagen) y ya están en Referencias (`pdfs/f[17].pdf`) |
| **Capurro et al. (2007)** | Cap. I › Bases teóricas › diagnóstico fitosanitario automatizado | La descripción del diagnóstico como "proceso inferencial que aumenta o disminuye la probabilidad" coincide con literatura de diagnóstico **médico** (probablemente Capurro, D. y Rada, G., *El proceso diagnóstico*, Rev Méd Chile, 2007) | a) Si esa es la fuente, reemplazarla por una de visión agrícola. b) Sustentar con Zhao et al. (2025) (`pdfs/[7].pdf`) o con Campos-Ferreira y González-Camacho (2021) (`pdfs/[1].pdf`) |

## 2. Fuentes reales que faltan en la carpeta `pdfs/` (descargar como respaldo)

Se agregaron en la nueva base teórica sobre YOLO y sus métricas, con referencia completa en el Word:

- [ ] Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). *You only look once: Unified, real-time object detection*. CVPR. https://doi.org/10.1109/CVPR.2016.91
- [ ] Jocher, G., & Qiu, J. (2024). *Ultralytics YOLO11* [Software]. https://github.com/ultralytics/ultralytics
- [ ] Padilla, R., Netto, S. L., & da Silva, E. A. B. (2020). *A survey on performance metrics for object-detection algorithms*. IWSSIP. https://doi.org/10.1109/IWSSIP48289.2020.9145130
- [ ] Wan, S., & Goudos, S. (2020). *Faster R-CNN for multi-class fruit detection using a robotic vision system*. Computer Networks, 168, 107036. https://doi.org/10.1016/j.comnet.2019.107036 (cita indirecta tomada de Narciso Horna y Manzano Ramos, 2021)
- [ ] Hernández Sampieri, R., Fernández Collado, C., & Baptista Lucio, M. del P. (2014). *Metodología de la investigación* (6.ª ed.). McGraw-Hill.
- [ ] Wang y He (2021): no hay PDF; verificar el dato de mAP 93.8 %.
- [ ] Blas Lozano et al. (2025), León León et al. (2020) y Campos Paredes (2025): no hay PDF. Los antecedentes regionales se recuperaron de `Tesis_Inicial.docx`; verificar sus datos.

## 3. Metas del Anexo 2 que todavía no tienen resultados

Se alineó solo la meta con resultados disponibles: **precisión del modelo** (alto ≥ 85 %, aceptable 70–84 %, bajo < 70 % en mAP50; HE1 ≥ 70 %).

Resultados en el split **test** (Cap. III, **v5**, 2 modelos): hojas = `hojas_tiempo_real` (YOLO11n, 640 px) mAP50 = 88.8 % (alto), exactitud 92.8 %; frutos (YOLO11s, 1024 px) mAP50 = 76.4 % (aceptable), exactitud 86.6 %. HE1 aceptada (p < 0.001); hojas también supera la meta del 85 %.

Pendientes de contrastar cuando estén los datos de campo:

| Dimensión | Meta actual en el Anexo 2 | Dato necesario |
|---|---|---|
| Velocidad de procesamiento | ≤ 150 ms por imagen | En CPU i7-12700: hojas 45 ms a 640 px (**cumple**), frutos 511 ms a 1024 px (**no cumple en CPU**). Medir en el servidor desplegado o redefinir la meta a ≤ 1 s por imagen |
| Capacidad de detección temprana | sensibilidad > 90 % (alta) | Ya calculada en el Cap. III, tablas 12 y 13. La tasa de detección va de 70.6 % a 97.1 %; las lesiones pequeñas (< 2 % del área) dan 0/17. **La meta de > 90 % no se cumple**: bajarla a ≥ 70 % o justificarlo |
| Precisión diagnóstica (VD) | coincidencia con el experto ≥ 85 % | Diagnóstico del agrónomo por árbol (pre y post) |
| Tiempo de inspección (VD) | reducción ≥ 50 % | Tiempos cronometrados por árbol (manual y con sistema) |
| Pérdidas por descarte (VD) | reducción ≥ 30 % | Conteos de frutos descartados y exportables |

## 4. Datos y evaluaciones para el Cap. III

- [x] Evaluar `hojas.pt` y `frutos.pt` en el split test: hecho, en `resultados-cap3/eval_test/`.
- [x] Matrices de confusión: las de Ultralytics 8.4 (`plots_*/confusion_matrix*.png`) usan conf = 0.001 y **no deben usarse**. Las válidas están en `figuras/cm_*.png` (umbral 0.35) y van en el Cap. III como Figuras 4 y 5.
- [ ] La corrida `frutos-entrenamiento/frutos_preciso` se **interrumpió** (no fue parada temprana) en la época 109 de 200, tras 5.0 h. Los checkpoints conservan el optimizador y la parada temprana recién tocaba en la época 133. Opcional: reanudarla con `YOLO('last.pt').train(resume=True)`.
- [ ] Limpiar `backend/models/frutos.pt` (76 MB, incluye el optimizador) con `strip_optimizer`; queda en unos 19 MB.
- [ ] La carpeta `frutos/hojas/` (corrida antigua de hojas) se borró del directorio de trabajo, pero sigue en git. Restaurarla con `git checkout -- frutos/hojas` o confirmar el borrado (ya la reemplaza `hojas-entrenamiento/`).
- [x] **Revisar `backend/models/hojas.pt`**: en el working tree (staged) ahora es el modelo YOLO11n de tiempo real (= `hojas_tiempo_real/weights/hojas.pt`), pero el backend lo corre a `yolo_imgsz` 1024. El commit db111520 tenía `hojas_preciso` (YOLO11s). Decidido (21/10): el modelo de hojas de la tesis es `hojas_tiempo_real` (640 px). Backend configurado (21/10): `yolo_imgsz_hojas` = 640 y `yolo_imgsz_frutos` = 1024 en `config.py` (variables `APP_YOLO_IMGSZ_HOJAS` / `APP_YOLO_IMGSZ_FRUTOS`). Falta actualizar las variables y el SHA256 de hojas en Railway.
- [ ] El modelo de tiempo real de hojas aún no está exportado a ONNX en `frontend/public/modelos/hojas.onnx` (el actual es de 38 MB, del 19/10). Exportar `hojas_tiempo_real` a ONNX 640 para que el Cap. III coincida con lo desplegado.
- [ ] Agregar Landis y Koch (1977) a las referencias (se cita en el Cap. III para interpretar κ).
- [ ] Las 18 inspecciones del PDF son del 7/10/2026, es decir, del modelo de frutos **anterior**. Repetir las inspecciones con el modelo nuevo.
- [ ] 6 de 18 registros (33 %) tenían mal seleccionado el órgano. Conviene validar el órgano automáticamente o mostrar una confirmación en la app.
- [ ] **Error en la app**: las acciones recomendadas muestran el texto de "sano" (mantener riego y fertilización) también en las inspecciones con alerta.
- [ ] Diagnóstico del agrónomo para las 12 inspecciones válidas (coincidencia con el experto).
- [ ] Descargar la base SQLite del **servidor desplegado** y la carpeta de imágenes. La `backend/plagas.db` local solo tiene 26 registros de prueba del 2026-10-07.
- [ ] Relacionar cada foto con su árbol y sector (A/B). La tabla `diagnosticos` no guarda el código del árbol, el diagnóstico del experto ni los tiempos.
- [ ] Actualizar `backend/models/manifest.json` (hoy solo registra `hojas.pt`).

## 5. Observaciones del Cap. II por corregir (no se tocaron todavía)

- [ ] Eliminar el argumento de las "200 mediciones": en un diseño pareado son 100 pares.
- [ ] Quitar el "$" suelto en "e = 0.10$".
- [ ] Quitar el párrafo duplicado de criterios de inclusión y exclusión en Población.
- [ ] "Dos dimensiones operativas" → son tres.
- [ ] Unificar los tiempos verbales (pasado).
- [ ] Para la precisión diagnóstica, usar McNemar y κ de Cohen; para tiempo y descarte, Shapiro-Wilk y luego t pareada o Wilcoxon.
- [ ] Aspectos éticos: "destrucción de datos" contradice la retención de imágenes por 365 días que tiene el sistema.
- [ ] Anexo 2: el resto de dimensiones figuran como "cuantitativa ordinal" y deberían ser continuas (solo se corrigió Precisión del modelo).
- [x] Numeración de tablas: corregida en el v3 (Cap. II: tablas 1 y 2; Cap. III desde la Tabla 3).
- [ ] Citar a Landis y Koch (1977) para la interpretación de κ (moderado/sustancial) del Cap. III y agregarlo a Referencias.
- [ ] Cap. IV (Discusión y conclusiones) sigue siendo la plantilla de la tesis de referencia.

## Datos simulados (v6, 21/10/2026)
- Las Tablas 11, 14 y 16 del Cap. III (tiempos, descarte y contraste de HE2/HE3) usan **datos simulados declarados como resultados esperados**: `resultados-cap3/simulacion/` (`simulacion.py` con semilla 2026, `datos_simulados_campo.xlsx`).
- [ ] En la tesis: reemplazar por las fichas de campo (mismas columnas del Excel) y volver a correr el análisis.
- [ ] Diagnóstico del especialista agrónomo sobre las fotos del historial: sigue pendiente; debe ser real.

## Instrumentos de campo (21/10/2026)
- `Instrumentos de recoleccion de datos - fichas de campo.docx`: protocolo + Fichas 1–4 + cuestionario (para anexos; poner el número de anexo en «Anexo __» y reemplazar el Anexo 3 de artesanos, que es de la plantilla).
- `resultados-cap3/simulacion/plantilla_vaciado_fichas_campo.xlsx`: vaciado con fórmulas (duraciones, % de descarte, promedio del cuestionario).
- Muestra: 100 árboles (50 A + 50 B), 5 hojas + 5 frutos por árbol (1,000 imágenes), 60 frutos por árbol para descarte, 200 imágenes para concordancia con el especialista.

## Fotos de ejemplo para el Cap. III (próxima semana)
- [ ] Tomar en campo con la app 4 a 6 fotos de ejemplo para figuras: hoja con antracnosis detectada, hoja con plagas, fruto con antracnosis/roña, fruto sano, un caso de error del sistema y una captura de la app en uso en el fundo.
- [ ] Exportar las capturas con las cajas de detección desde el historial y pasármelas para insertarlas como figuras (con su nota APA) en la sección «Verificación en campo con el sistema desplegado».
- `Fichas 1 y 2 - ejemplo de llenado (datos simulados).docx`: ejemplo de llenado marcado como datos simulados (árboles A-01 a A-08 de `datos_simulados_campo.xlsx`); sirve para mostrar cómo se completa cada ficha.
- v8 (`... - v8 Cap III resultados y anexos.docx`): Fichas 1 y 2 de ejemplo insertadas como **Anexos 7 y 8** (páginas horizontales, marcadas como datos simulados). Actualizar el índice de anexos con Ctrl+A → F9 → «Actualizar toda la tabla».

## v9 (22/10/2026): coherencia Cap. I–II y Anexo 2
- Archivo: `... - v9 Cap I-II coherencia.docx` (cambios anteriores ya aceptados; solo quedan marcadas las correcciones nuevas; script `resultados-cap3/edit_v9.py`).
- Anexo 2 alineado: metas de reducción ≥ 30 % (tiempo) y ≥ 15 % (descarte); velocidad ≤ 150 ms (tiempo real, hojas) / ≤ 1,000 ms (servidor, frutos).
- [ ] Sin tocar a pedido del usuario: Resumen/Abstract, Cap. IV, Anexo 1, Anexos 3–6 (artesanos), referencias (MIDAGRI, CONCYTEC, Landis y Koch).
