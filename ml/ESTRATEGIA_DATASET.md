# Estrategia del dataset: detección de enfermedades en palta Hass

Documento de trabajo con el análisis del dataset, las decisiones tomadas y cómo regenerar los datasets de entrenamiento.

---

## 1. Resumen

- **Fuente:** `DatasetOriginal/` exportado de Roboflow Universe (`avocado-disease-master` v1, CC BY 4.0), 6,448 imágenes de 1024×1024 ("Fit (black edges)"), formato YOLOv11.
- **Estrategia:** **dos modelos YOLO11 de detección**, uno para **hojas** y otro para **frutos**. En la app el usuario elige "Hoja" o "Fruto" antes de tomar la foto.
- **Por qué dos modelos:** las enfermedades atacan órganos distintos. Separarlos reduce la confusión entre clases y permite mejorar cada modelo por separado.
- **Sin dataset propio:** no se fotografía ni se etiqueta nada nuevo. Todo sale de reorganizar y limpiar el dataset original.
- **Modelo:** YOLO11 (`yolo11s` o `yolo11m`) con `task=detect` e `imgsz=1024`. El cuello de botella es la calidad del dataset, no la versión de YOLO.

---

## 2. Hallazgos del análisis

### 2.1 El YAML con números (`Dataset/`, export de 640)
El primer export tenía `names: ['0','1','10','11',...]`. Roboflow guardó **el índice original como nombre** y luego lo ordenó como texto. Por ejemplo, la clase con nombre `'9'` es `nutrient_deficiency`. Las etiquetas eran coherentes, pero los nombres no servían. Ese dataset queda **reemplazado** por `DatasetOriginal/`, que además está a 1024 px.

### 2.2 Clases originales y órgano real (verificado visualmente)

| # | Clase original | Anotación | Órgano real | Cajas |
|---|---|---|---|---|
| 0 | Anthracnose | polígono | **hoja** (campo) | 694 |
| 0 | Anthracnose | caja | **fruto** (internet) | 1457 |
| 1 | Healthy | polígono | **hoja** | 694 |
| 1 | Healthy | caja | **fruto** (incluye clipart) | 1182 |
| 2 | Pest Infested | polígono | hoja completa | 700 |
| 3 | Pest attack | caja | lesiones pequeñas en hoja | 76 |
| 4 | Stem End Rot | caja | fruto | 7 |
| 5 | algal_leaf_spot | caja | hoja (lesiones ~47 px) | 48 |
| 6 | anthracnose | polígono | fruto (supermercado) | 500 |
| 7 | cercospora_spot | caja | fruto | 1129 |
| 8 | healthy | polígono | fruto (supermercado, varios maduros/negros) | 586 |
| 9 | nutrient_deficiency | polígono | hoja | 700 |
| 10 | persea_mite | caja | hoja | 32 |
| 11 | powdery_mildew | caja | hoja (lesiones ~37 px) | 33 |
| 12 | scab | polígono | fruto | 510 |
| 13 | stem end rot | polígono | fruto | 453 |
| 14 | sunblotch | caja | fruto | 443 |

**Conclusiones:**
- La mayúscula o minúscula del nombre **no indica el órgano**. Indica de qué dataset fuente vino la clase, porque Roboflow juntó varios datasets sin unificar nombres.
- En `Anthracnose` y `Healthy`, el **tipo de anotación sí separa el órgano**: polígono = hoja y caja = fruto. Solo 6 imágenes del dataset completo tienen caja y polígono de la misma clase a la vez.
- Mezclar cajas y polígonos **no es un problema** para `task=detect`: YOLO convierte el polígono a la caja que lo encierra. Igualmente, el script convierte todo a cajas para que el dataset quede uniforme.

### 2.3 Problemas encontrados
1. **Fuga de datos (data leakage).** Había fotos idénticas o casi idénticas repartidas entre train y valid/test: 23 grupos de imágenes idénticas, 80 fotos con el mismo nombre original en varios splits y muchas ráfagas del mismo fruto u hoja. El modelo las memoriza en el entrenamiento y luego las "acierta" en el test, así que las métricas salen infladas.
2. **Split no estratificado.** Roboflow divide al azar por imagen. Por ejemplo, `Stem End Rot` quedó 7/0/0 y `persea_mite` 30/1/1.
3. **Clases muy pequeñas.** `algal_leaf_spot`, `persea_mite` y `powdery_mildew` tienen entre 32 y 48 cajas, con lesiones diminutas tomadas en una sola sesión (hojas sobre cemento).
4. **Criterios de anotación distintos.** `Pest Infested` marca la hoja completa y `Pest attack` marca lesiones pequeñas.
5. **Fruta negra o madura etiquetada como sana.** Para exportación la palta se cosecha **verde**, así que un fruto negro indica un problema. Sin embargo, `healthy` y `Healthy` (cajas) tienen fruta madura y negra, además de clipart e infografías.

---

## 3. Decisiones tomadas

| Decisión | Motivo |
|---|---|
| Separar en `DatasetHojas` y `DatasetFrutos` | Las enfermedades son específicas de cada órgano |
| Separar `Anthracnose`/`Healthy` por tipo de anotación | Polígono = hoja, caja = fruto (verificado) |
| Descartar `algal_leaf_spot`, `persea_mite`, `powdery_mildew` | Muy pocas muestras para aprenderlas |
| Descartar `Pest attack`; `plaga` = solo `Pest Infested` | Criterio de anotación distinto (lesión frente a hoja completa); `Pest Infested` ya tiene 700 cajas |
| Unir `Stem End Rot` + `stem end rot` | Misma enfermedad de fruto (la primera tiene solo 7 cajas) |
| Revisión manual de `fruto_sano` con galería | Quitar fruta negra o madura y clipart |
| Convertir todos los polígonos a cajas | Dataset uniforme para `task=detect` |
| Split 70/20/10 por grupos y estratificado | Elimina la fuga y equilibra las clases entre splits |

### 3.1 Mapeo final de clases

**Modelo HOJAS** (`DatasetHojas/data.yaml`)

| id | Clase | Sale de |
|---|---|---|
| 0 | `hoja_sana` | `Healthy` (polígonos) |
| 1 | `antracnosis_hoja` | `Anthracnose` (polígonos) |
| 2 | `plaga` | `Pest Infested` |
| 3 | `deficiencia_nutricional` | `nutrient_deficiency` |

**Modelo FRUTOS** (`DatasetFrutos/data.yaml`)

| id | Clase | Sale de |
|---|---|---|
| 0 | `fruto_sano` | `Healthy` (cajas) + `healthy` − imágenes excluidas en la revisión |
| 1 | `antracnosis_fruto` | `Anthracnose` (cajas) + `anthracnose` |
| 2 | `cercospora` | `cercospora_spot` |
| 3 | `rona` | `scab` |
| 4 | `pudricion_peduncular` | `Stem End Rot` + `stem end rot` |
| 5 | `sunblotch` | `sunblotch` |

El mapeo está definido en `scripts/comun.py` (`_MAPEO`). Si se quiere recuperar una clase descartada, basta con cambiar su `None` por `(organo, clase)` y agregar la clase en `CLASES`.

---

## 4. Cómo se detectan duplicados y casi-duplicados

Para cada imagen se calculan:
- **dHash de 256 bits**: describe la estructura de la imagen en escala de grises.
- **Miniatura de color de 32×32**: para comparar el color **ignorando el fondo blanco o gris y el relleno negro**. Sin esto, frutos distintos sobre fondo blanco se veían "iguales".

Dos imágenes van al **mismo grupo** si:
- tienen el mismo nombre original (antes del `_jpg.rf.<hash>` de Roboflow), o
- su dHash difiere en 16 bits o menos **y** su diferencia de color es menor a 10 (en escala 0–255). Estos umbrales se calibraron mirando pares reales: por debajo de 10 eran ráfagas de la misma escena, y por encima de 14 eran frutos distintos.

Además:
- Las fotos de mesa giratoria `P<n>_<grados>-degrees` se agrupan **por fruto (`P<n>`)**. Antes, el fondo gris común unía 187 imágenes de frutos distintos en un solo grupo.
- **Copias exactas** (dHash idéntico y color prácticamente igual): se deja una sola copia, la que tiene más anotaciones. Se descartaron 60.

Un grupo completo siempre va a **un solo split**. Así ninguna foto del test tiene una "gemela" en train.

---

## 5. Cómo regenerar los datasets

Requisitos: Python 3.10+, `numpy` y `Pillow`.

```bash
# 1) Generar la galería de revisión de fruto_sano
python scripts/01_galeria_fruto_sano.py
#    -> revision/galeria_fruto_sano.html  (abrir en el navegador)

# 2) Revisar a mano en la galería:
#    - recuadro verde = fruto sano; recuadro rojo = fruto con su enfermedad (no se toca)
#    - clic en una imagen = EXCLUIR sus recuadros verdes (fruta negra/madura, clipart, infografías…)
#    - están ordenadas de más oscura a menos oscura; "sugerida" = puntaje >= 0.5 (solo una ayuda)
#    - las marcas se guardan en el navegador (puedes cerrar y seguir después)
#    - al terminar: "Descargar excluir_fruto_sano.txt" y guardarlo en revision/

# 3) Construir los datasets
python scripts/02_preparar_datasets.py
#    -> DatasetHojas/ y DatasetFrutos/ (se borran y regeneran en cada ejecución)
#    -> revision/reporte_preparacion.json (conteos por clase y split)
```

`--sin-revision` genera los datasets sin el archivo de exclusiones. Sirve solo para pruebas: ya no se usa porque la revisión está hecha.

Otras opciones: `--semilla 42` y `--proporciones 0.7 0.2 0.1`.

Al excluir una imagen se quitan solo sus cajas de `fruto_sano`. Si no tenía otras etiquetas, la imagen sale completa. Si tenía frutos con otra enfermedad, se conserva con esas etiquetas (ver 6.1).

---

## 6. Resultado final (con revisión de `fruto_sano`, 2026-10-06)

Revisión manual: **334 imágenes marcadas** de 1,063 con `fruto_sano`. Se descartaron además 60 copias exactas.

### 6.1 Corrección de la regla de exclusión
En la primera versión, una imagen marcada se quitaba **completa**. Pero muchas fotos, sobre todo de supermercado, tienen varios frutos: uno etiquetado como sano y otros, en la misma foto, con antracnosis, roña, etc. La galería solo dibujaba el recuadro del fruto sano, así que **los frutos enfermos de esas fotos parecían "sanos mal etiquetados"**. Al excluir la imagen se perdían también sus etiquetas de enfermedad: 102 imágenes de `antracnosis_fruto`, 54 de `rona`, 19 de `pudricion_peduncular`, 3 de `sunblotch` y 1 de `cercospora`.

**Regla actual:**
- Si la imagen marcada **solo tiene `fruto_sano`**, sale completa (206 imágenes).
- Si **también tiene frutos con otra enfermedad**, se conserva la imagen con esas etiquetas y solo se quitan sus cajas de `fruto_sano` (128 imágenes).

La galería ahora dibuja los frutos enfermos en **rojo con el nombre de su enfermedad**, para que no se confundan con frutos sanos.

### 6.2 Conteos

**DatasetHojas:** 2,380 imágenes en 1,338 grupos (train 1,657 / valid 486 / test 237)

| Clase | train | valid | test | % |
|---|---|---|---|---|
| hoja_sana | 485 | 138 | 69 | 70/20/10 |
| antracnosis_hoja | 484 | 140 | 69 | 70/20/10 |
| plaga | 489 | 142 | 68 | 70/20/10 |
| deficiencia_nutricional | 488 | 140 | 70 | 70/20/10 |

**DatasetFrutos:** 3,716 imágenes en 2,731 grupos (train 2,545 / valid 790 / test 381)

| Clase | train | valid | test | % |
|---|---|---|---|---|
| fruto_sano | 726 | 206 | 104 | 70/20/10 |
| antracnosis_fruto | 1349 | 386 | 192 | 70/20/10 |
| cercospora | 782 | 224 | 112 | 70/20/10 |
| rona | 357 | 100 | 53 | 70/20/10 |
| pudricion_peduncular | 325 | 78 | 34 | 74/18/8 |
| sunblotch | 304 | 88 | 40 | 70/20/9 |

(Valores en cajas.) Las clases de enfermedad conservan prácticamente todas sus anotaciones; las pequeñas diferencias frente a antes se deben a que el split por grupos se recalcula. `fruto_sano` bajó de 1,764 a 1,036 cajas en total.

**Nota:** 297 imágenes de `fruto_sano` (19 frutos distintos) son de la serie de mesa giratoria `P<n>_<grados>-degrees`: el mismo fruto fotografiado girando, sobre fondo gris. Eso da poca variedad a esa clase.

---

## 7. Entrenamiento recomendado

```bash
yolo task=detect mode=train model=yolo11s.pt data=<ruta>/DatasetHojas/data.yaml  epochs=150 imgsz=1024 patience=30 batch=-1 plots=True
yolo task=detect mode=train model=yolo11s.pt data=<ruta>/DatasetFrutos/data.yaml epochs=150 imgsz=1024 patience=30 batch=-1 plots=True
```

- `epochs=10` (lo que trae el notebook) es muy poco. Con `patience=30` el entrenamiento se detiene solo cuando deja de mejorar.
- `imgsz=1024` aprovecha la resolución del export. En una GPU T4 de Colab, `batch=-1` ajusta el tamaño del lote solo.
- Si `yolo11s` queda corto, probar `yolo11m`.
- **En Colab o en otra PC:** editar `path:` en `data.yaml` con la ruta real del dataset y pasar la ruta **absoluta** del yaml.
- Evaluar con `mode=val split=test` **una sola vez al final**. Para comparar experimentos se usa `valid`.

---

## 8. Pendientes y riesgos conocidos

- [x] Revisar la galería de `fruto_sano` y regenerar los datasets (hecho el 2026-10-06: 334 excluidas).
- [ ] Entrenar ambos modelos y revisar la matriz de confusión: vigilar `antracnosis_fruto` frente a `pudricion_peduncular` y `fruto_sano` frente a `cercospora`.
- Gran parte del dataset de frutos viene de **internet o supermercado**, no de campo. Conviene probar con fotos reales del uso previsto antes de confiar en las métricas.
- En las fotos de supermercado no todos los frutos visibles están anotados. Eso agrega algo de ruido, que es aceptable.
- Las clases descartadas (`algal_leaf_spot`, `persea_mite`, `powdery_mildew`) se pueden recuperar más adelante si se consiguen más datos, por ejemplo de otros datasets de Roboflow Universe.

---

## 9. Estructura de archivos

```
DatasetOriginal/              export original de Roboflow (no se modifica)
Dataset/                      export antiguo a 640 px con nombres numéricos (obsoleto)
scripts/
  comun.py                    clases, mapeo y lectura de etiquetas
  01_galeria_fruto_sano.py    genera la galería de revisión
  02_preparar_datasets.py     construye DatasetHojas/ y DatasetFrutos/
revision/
  galeria_fruto_sano.html     galería (abrir en navegador)
  galeria_fruto_sano/         miniaturas de la galería
  excluir_fruto_sano.txt      (lo creas tú desde la galería)
  reporte_preparacion.json    conteos del último armado
DatasetHojas/                 generado (4 clases)
DatasetFrutos/                generado (6 clases)
```
