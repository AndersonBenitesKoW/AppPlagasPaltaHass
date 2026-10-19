# Pendientes de la tesis

Documento de trabajo: `OPTIMIZACION DE PRODUCCION DE PALTA HASS - v2 Cap I corregido.docx` (copia con control de cambios; el original no se modificó).

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

Se alineó solo la meta con resultados disponibles: **precisión del modelo** (alto ≥ 85 %, aceptable 70–84 %, bajo < 70 % en mAP50; HE1 ≥ 70 %). Resultados en el split de validación: hojas mAP50 = 0.916 (alto) y frutos mAP50 = 0.793 (aceptable).

Pendientes de contrastar cuando estén los datos de campo:

| Dimensión | Meta actual en el Anexo 2 | Dato necesario |
|---|---|---|
| Velocidad de procesamiento | ≤ 150 ms por imagen | Medir el tiempo de inferencia en el servidor desplegado |
| Capacidad de detección temprana | sensibilidad > 90 % (alta) | Recall por clase en el split test |
| Precisión diagnóstica (VD) | coincidencia con el experto ≥ 85 % | Diagnóstico del agrónomo por árbol (pre y post) |
| Tiempo de inspección (VD) | reducción ≥ 50 % | Tiempos cronometrados por árbol (manual y con sistema) |
| Pérdidas por descarte (VD) | reducción ≥ 30 % | Conteos de frutos descartados y exportables |

## 4. Datos y evaluaciones para el Cap. III

- [ ] Evaluar `hojas.pt` y `frutos.pt` en el **split test** (`yolo val split=test`) con métricas por clase. Las métricas actuales son del split de validación.
- [ ] Subir la carpeta de la corrida de **frutos** (results.csv, matriz de confusión, curvas PR/F1). La carpeta `frutos/hojas/` contiene la corrida de **hojas**.
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
- [ ] Numeración de tablas: el Cap. II empieza en "Tabla 2".
