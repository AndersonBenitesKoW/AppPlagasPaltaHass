"""Matriz de confusion en test con el umbral operativo del sistema (conf = 0.35) y tambien 0.25 (referencia)."""
import json, sys
from pathlib import Path
from ultralytics import YOLO

S = Path(__file__).parent
ROOT = Path("D:/AppWebPlagasPaltaHass")
PESOS = {"frutos": ROOT / "backend/models/frutos.pt", "hojas": ROOT / "hojas-entrenamiento/hojas_preciso/weights/best.pt",
         "hojas_rt": ROOT / "hojas-entrenamiento/hojas_tiempo_real/weights/hojas.pt"}
IMG = {"hojas_rt": 640}

out = json.loads((S / "cm_test.json").read_text(encoding="utf8"))
for nombre in sys.argv[1:] or ["frutos", "hojas"]:
    m = YOLO(str(PESOS[nombre]))
    out[nombre] = {}
    for conf in (0.25, 0.35):
        r = m.val(data=str(S / f"data_{nombre.split('_')[0]}.yaml"), split="test", imgsz=IMG.get(nombre, 1024), batch=8, device="cpu", conf=conf,
                  plots=True, project=str(S / "eval_cm"), name=f"{nombre}_conf{int(conf * 100)}", exist_ok=True, verbose=False)
        cm = r.confusion_matrix
        out[nombre][str(conf)] = {"names": list(m.names.values()), "matrix": cm.matrix.astype(int).tolist()}
        print(nombre, conf, cm.matrix.astype(int).tolist(), flush=True)
(S / "cm_test.json").write_text(json.dumps(out, indent=1), encoding="utf8")
