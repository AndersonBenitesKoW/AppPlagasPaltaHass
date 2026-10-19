"""Exporta los pesos de backend/models/*.pt a ONNX para la detección en tiempo real del frontend.

Salida: frontend/public/modelos/<nombre>.onnx y frontend/public/modelos/modelos.json
(clases e imgsz que lee el navegador).

Uso (desde la raíz del repo):
    cd backend && uv run --with onnx --with onnxslim python ../ml/scripts/03_exportar_onnx.py
"""
import json
import shutil
import sys
from pathlib import Path

from ultralytics import YOLO

RAIZ_REPO = Path(__file__).resolve().parents[2]
MODELOS = RAIZ_REPO / "backend" / "models"
DESTINO = RAIZ_REPO / "frontend" / "public" / "modelos"

# 640 px: compromiso velocidad/precisión en celulares. El diagnóstico que se guarda
# lo vuelve a calcular el backend a 1024 px.
IMGSZ = int(sys.argv[1]) if len(sys.argv) > 1 else 640
ORGANOS = {"hoja": "hojas", "fruto": "frutos"}


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    manifiesto: dict[str, dict[str, object]] = {}

    for organo, nombre in ORGANOS.items():
        pt = MODELOS / f"{nombre}.pt"
        if not pt.exists():
            print(f"[omitido] {pt} no existe")
            continue

        modelo = YOLO(str(pt))
        ruta_onnx = Path(modelo.export(format="onnx", imgsz=IMGSZ, simplify=True, opset=17, dynamic=False))
        shutil.move(str(ruta_onnx), DESTINO / f"{nombre}.onnx")

        nombres = modelo.names
        manifiesto[organo] = {
            "archivo": f"{nombre}.onnx",
            "imgsz": IMGSZ,
            "clases": [nombres[i] for i in sorted(nombres)],
        }
        print(f"[ok] {organo}: {DESTINO / f'{nombre}.onnx'}")

    (DESTINO / "modelos.json").write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[ok] {DESTINO / 'modelos.json'}")


if __name__ == "__main__":
    main()
