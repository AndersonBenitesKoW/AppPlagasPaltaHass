import io
import threading
from pathlib import Path
from typing import Any

import anyio
from PIL import Image as PILImage
from ultralytics import YOLO  # type: ignore[attr-defined]

from plagas.modules.diagnostico.domain.value_objects import (
    CajaDelimitadora,
    Confianza,
    Deteccion,
    Imagen,
)


class DetectorYolo:
    """Implementa DetectorEnfermedades con un modelo Ultralytics YOLO."""

    def __init__(self, ruta_pesos: Path, imgsz: int = 1024, conf_minima: float = 0.10) -> None:
        self._modelo: Any = YOLO(str(ruta_pesos))
        self._imgsz = imgsz
        self._conf_minima = conf_minima
        self._lock = threading.Lock()

    async def detectar(self, imagen: Imagen) -> list[Deteccion]:
        return await anyio.to_thread.run_sync(self._predecir, imagen.contenido)

    def _predecir(self, contenido: bytes) -> list[Deteccion]:
        pil = PILImage.open(io.BytesIO(contenido)).convert("RGB")
        with self._lock:
            prediccion: Any = self._modelo.predict(
                pil,
                imgsz=self._imgsz,
                conf=self._conf_minima,
                verbose=False,
            )
            resultado: Any = prediccion[0]

        nombres = resultado.names
        cajas = resultado.boxes
        if cajas is None or len(cajas) == 0:
            return []

        salida: list[Deteccion] = []
        for xyxyn, conf, cls_idx in zip(
            cajas.xyxyn.tolist(),
            cajas.conf.tolist(),
            cajas.cls.tolist(),
            strict=False,
        ):
            x1, y1, x2, y2 = xyxyn
            # Asegurar rango 0..1
            x1 = max(0.0, min(1.0, float(x1)))
            y1 = max(0.0, min(1.0, float(y1)))
            x2 = max(0.0, min(1.0, float(x2)))
            y2 = max(0.0, min(1.0, float(y2)))
            clase_nombre = str(nombres.get(int(cls_idx), f"clase_{int(cls_idx)}"))

            salida.append(
                Deteccion(
                    clase=clase_nombre,
                    confianza=Confianza(round(float(conf), 4)),
                    caja=CajaDelimitadora(x1=x1, y1=y1, x2=x2, y2=y2),
                )
            )
        return salida
