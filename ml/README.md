# ML — Entrenamiento y datasets

Todo lo relacionado al modelo vive aquí, **fuera** de los contenedores que
corren la app en producción.

## Estructura

```
ml/
├── notebooks/        # Jupyter notebooks de entrenamiento (YOLO11)
├── scripts/          # Scripts auxiliares de preparación de datos
├── datasets/         # Datasets (git-ignored; datos crudos y splits)
├── revision/         # Salidas de revisión/galería (git-ignored)
├── runs/             # Salidas de entrenamiento (git-ignored)
└── ESTRATEGIA_DATASET.md
```

## Reproducir el entrenamiento

1. Activar Python 3.12 (`pyenv local 3.12` desde la raíz).
2. Instalar deps de entrenamiento:
   ```bash
   uv pip install --python 3.12 ultralytics>=8.3 torch>=2.5 pillow>=11
   ```
3. Abrir `notebooks/train_yolo11_object_detection_on_custom_dataset.ipynb`
   en Colab o local con Jupyter.
4. El notebook apunta a `datasets/DatasetHojas/data.yaml` y
   `datasets/DatasetFrutos/data.yaml`.

## Reentrenamiento robusto a distancia y enfoque

`notebooks/reentrenamiento_robusto_yolo11.ipynb` entrena dos variantes por órgano
con aumentación de cámara de campo (escala, desenfoque, ruido, compresión, luz):

- `preciso` (YOLO11s@1024) → `backend/models/*.pt`
- `tiempo_real` (YOLO11n@640) → `frontend/public/modelos/*.onnx`

Incluye un benchmark que compara el modelo actual y el nuevo con objetos más
lejanos y desenfocados, y exporta todo listo para copiar al repo.

## Promover un modelo a producción

Antes de mover `best.pt` a `backend/models/`, **siempre**:

1. Correr `yolo val` sobre el split `test` del dataset correspondiente.
2. Comparar mAP50-95 y recall por clase contra el `manifest.json` vigente.
3. Si mejora o se mantiene dentro de tolerancia, copiar el `.pt` a
   `backend/models/<nombre>.pt`.
4. Actualizar `backend/models/manifest.json` con la nueva versión, fecha,
   métricas y SHA-256.
5. Commitear el `manifest.json` (el `.pt` no se versiona; el contenedor
   lo obtiene por volumen o por descarga en CI).

## Regla de nombres

| Órgano | Archivo de pesos | Dataset |
|---|---|---|
| Hoja | `hojas.pt` | `DatasetHojas` (4 clases) |
| Fruto | `frutos.pt` | `DatasetFrutos` (6 clases) |

## Scripts auxiliares

- `scripts/01_galeria_fruto_sano.py` — genera galería HTML de la clase
  `fruto_sano` para auditoría humana.
- `scripts/02_preparar_datasets.py` — produce los splits `train/valid/test`
  en formato YOLO. Genera `data.yaml` por dataset.
- `scripts/comun.py` — utilidades compartidas.

Las salidas de estos scripts viven en `revision/` y `datasets/`.
