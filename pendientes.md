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

Resultados en el split **test** (Cap. III): hojas mAP50 = 84.8 % (aceptable, a 0.2 puntos del nivel alto) y frutos mAP50 = 76.4 % (aceptable). En validación eran 91.6 % y 78.7 %. La HE1 se acepta con la prueba binomial (p < 0.001).

Pendientes de contrastar cuando estén los datos de campo:

| Dimensión | Meta actual en el Anexo 2 | Dato necesario |
|---|---|---|
| Velocidad de procesamiento | ≤ 150 ms por imagen | En CPU i7-12700 se midieron 176 ms (hojas) y 511 ms (frutos), así que la meta **no se cumple en CPU**. Medir en el servidor desplegado o redefinir la meta a ≤ 1 s por imagen |
| Capacidad de detección temprana | sensibilidad > 90 % (alta) | Ya calculada en el Cap. III, tablas 12 y 13. La tasa de detección va de 70.6 % a 97.1 %; las lesiones pequeñas (< 2 % del área) dan 0/17. **La meta de > 90 % no se cumple**: bajarla a ≥ 70 % o justificarlo |
| Precisión diagnóstica (VD) | coincidencia con el experto ≥ 85 % | Diagnóstico del agrónomo por árbol (pre y post) |
| Tiempo de inspección (VD) | reducción ≥ 50 % | Tiempos cronometrados por árbol (manual y con sistema) |
| Pérdidas por descarte (VD) | reducción ≥ 30 % | Conteos de frutos descartados y exportables |

## 4. Datos y evaluaciones para el Cap. III

- [x] Evaluar `hojas.pt` y `frutos.pt` en el split test: hecho, en `resultados-cap3/eval_test/`.
- [x] Matrices de confusión: las de Ultralytics 8.4 (`plots_*/confusion_matrix*.png`) usan conf = 0.001 y **no deben usarse**. Las válidas están en `figuras/cm_*.png` (umbral 0.35) y van en el Cap. III como Figuras 4 y 5.
- [ ] La corrida `frutos-entrenamiento/frutos_preciso` se **interrumpió** (no fue parada temprana) en la época 109 de 200, tras 5.0 h. Los checkpoints conservan el optimizador y la parada temprana recién tocaba en la época 133. Opcional: reanudarla con `YOLO('last.pt').train(resume=True)`.
- [ ] Limpiar `backend/models/frutos.pt` (76 MB, incluye el optimizador) con `strip_optimizer`; queda en unos 19 MB.
- [ ] La carpeta `frutos/hojas/` (corrida de hojas) se borró del directorio de trabajo, pero sigue en git. Restaurarla con `git checkout -- frutos/hojas`.
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
