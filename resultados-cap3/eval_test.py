"""Evaluacion en split test: metricas por clase, diagnostico por imagen y sensibilidad por tamano de lesion."""
import json, math, sys, time
from pathlib import Path
import numpy as np
from ultralytics import YOLO

S = Path(__file__).parent
ROOT = Path("D:/AppWebPlagasPaltaHass")
CONF = 0.35  # umbral del backend (config.py)
IMGSZ = 1024

CFG = {
    "frutos": (ROOT / "backend/models/frutos.pt", ROOT / "ml/datasets/DatasetFrutos",
               ["fruto_sano", "antracnosis_fruto", "cercospora", "rona", "pudricion_peduncular", "sunblotch"]),
    "hojas": (ROOT / "hojas-entrenamiento/hojas_preciso/weights/best.pt", ROOT / "ml/datasets/DatasetHojas",
              ["hoja_sana", "antracnosis_hoja", "plaga", "deficiencia_nutricional"]),
    "hojas_rt": (ROOT / "hojas-entrenamiento/hojas_tiempo_real/weights/hojas.pt", ROOT / "ml/datasets/DatasetHojas",
                 ["hoja_sana", "antracnosis_hoja", "plaga", "deficiencia_nutricional"]),
}
IMG = {"hojas_rt": 640}  # modelo ligero de tiempo real (yolo11n a 640)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    i = max(0, x2 - x1) * max(0, y2 - y1)
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u > 0 else 0


def xywh2xyxy(x, y, w, h):
    return [x - w / 2, y - h / 2, x + w / 2, y + h / 2]


def run(nombre):
    pesos, ds, clases = CFG[nombre]
    IMGSZ = IMG.get(nombre, 1024)
    yml = S / f"data_{nombre}.yaml"
    yml.write_text(f"path: {ds.as_posix()}\ntrain: train/images\nval: valid/images\ntest: test/images\n"
                   f"nc: {len(clases)}\nnames: {json.dumps(clases)}\n", encoding="utf8")
    m = YOLO(str(pesos))
    out = {"modelo": nombre}

    # 1) validacion estandar en test
    r = m.val(data=str(yml), split="test", imgsz=IMGSZ, batch=8, device="cpu", plots=True,
              project=str(S / "eval"), name=nombre, exist_ok=True, verbose=True)
    p, rc, m50, m5095 = r.box.mp, r.box.mr, r.box.map50, r.box.map
    out["global"] = dict(P=p, R=rc, F1=2 * p * rc / (p + rc), mAP50=m50, mAP50_95=m5095)
    out["por_clase"] = {}
    for i, c in enumerate(r.box.ap_class_index):
        pc, rcc, a50, a = r.box.class_result(i)
        out["por_clase"][clases[c]] = dict(P=pc, R=rcc, F1=2 * pc * rcc / (pc + rcc) if pc + rcc else 0,
                                          mAP50=a50, mAP50_95=a)
    out["speed_val_ms"] = r.speed

    # 2) diagnostico por imagen y 3) sensibilidad por tamano
    imgs = sorted((ds / "test/images").glob("*"))
    TP = FP = FN = TN = 0
    por_enf = {c: [0, 0] for c in clases[1:]}  # [detectada, presente]
    tam = {"pequena (<2%)": [0, 0], "mediana (2-10%)": [0, 0], "grande (>10%)": [0, 0]}
    tiempos = []
    for im in imgs:
        lab = ds / "test/labels" / (im.stem + ".txt")
        gt = [list(map(float, l.split())) for l in lab.read_text().split("\n") if l.strip()] if lab.exists() else []
        t0 = time.perf_counter()
        res = m.predict(str(im), imgsz=IMGSZ, conf=CONF, device="cpu", verbose=False)[0]
        tiempos.append((time.perf_counter() - t0) * 1000)
        pb = res.boxes.xyxyn.cpu().numpy().tolist()
        pc = res.boxes.cls.cpu().numpy().astype(int).tolist()
        gt_enf = any(int(g[0]) != 0 for g in gt)
        pr_enf = any(c != 0 for c in pc)
        TP += gt_enf and pr_enf; FN += gt_enf and not pr_enf
        FP += (not gt_enf) and pr_enf; TN += (not gt_enf) and not pr_enf
        for c in {int(g[0]) for g in gt if int(g[0]) != 0}:
            por_enf[clases[c]][1] += 1
            por_enf[clases[c]][0] += c in pc
        for g in gt:
            if int(g[0]) == 0:
                continue
            gb = xywh2xyxy(*g[1:5])
            area = g[3] * g[4]
            k = "pequena (<2%)" if area < 0.02 else "mediana (2-10%)" if area <= 0.10 else "grande (>10%)"
            tam[k][1] += 1
            tam[k][0] += any(c == int(g[0]) and iou(gb, b) >= 0.5 for b, c in zip(pb, pc))
    n = TP + FP + FN + TN
    po = (TP + TN) / n
    pe = ((TP + FP) * (TP + FN) + (FN + TN) * (FP + TN)) / (n * n)
    out["imagen"] = dict(n=n, TP=TP, FP=FP, FN=FN, TN=TN,
                         sensibilidad=wilson(TP, TP + FN), especificidad=wilson(TN, TN + FP),
                         exactitud=wilson(TP + TN, n), vpp=wilson(TP, TP + FP), vpn=wilson(TN, TN + FN),
                         kappa=(po - pe) / (1 - pe) if pe < 1 else float("nan"))
    out["deteccion_por_enfermedad"] = {k: dict(detectadas=v[0], presentes=v[1], tasa=wilson(*v)) for k, v in por_enf.items()}
    out["sensibilidad_por_tamano"] = {k: dict(detectadas=v[0], total=v[1], tasa=wilson(*v)) for k, v in tam.items()}
    t = np.array(tiempos[3:])  # descartar calentamiento
    out["tiempo_ms"] = dict(media=float(t.mean()), de=float(t.std(ddof=1)), mediana=float(np.median(t)),
                            p95=float(np.percentile(t, 95)), n=int(len(t)))
    (S / f"eval_{nombre}.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf8")
    print(json.dumps(out, indent=2, default=float))


if __name__ == "__main__":
    for n in sys.argv[1:] or ["frutos", "hojas"]:
        run(n)
