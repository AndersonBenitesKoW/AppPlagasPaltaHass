"""Figuras del Cap. III (estilo sobrio, Times New Roman, escala de grises + un acento)."""
import csv, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

S = Path(__file__).parent
F = S / "fig"
F.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "Times New Roman", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 220, "savefig.bbox": "tight"})
VERDE, GRIS = "#2E6B3F", "#8C8C8C"

ETQ = {"fruto_sano": "Fruto sano", "antracnosis_fruto": "Antracnosis (fruto)", "cercospora": "Cercospora",
       "rona": "Roña", "pudricion_peduncular": "Pudrición peduncular", "sunblotch": "Sunblotch",
       "hoja_sana": "Hoja sana", "antracnosis_hoja": "Antracnosis (hoja)", "plaga": "Plagas (trips/ácaros)",
       "deficiencia_nutricional": "Deficiencia nutricional"}


def flujo():
    pasos = ["Captura de imagen\n(cámara o galería)", "Selección del órgano\n(hoja / fruto)",
             "Inferencia YOLO11s\n(modelo hojas o frutos)", "Filtro de confianza\n(≥ 0.35)",
             "Veredicto y acciones\nrecomendadas", "Registro en historial\n(SQLite) y reporte PDF"]
    fig, ax = plt.subplots(figsize=(6.3, 7.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, len(pasos) * 1.6); ax.axis("off")
    for i, p in enumerate(pasos):
        y = (len(pasos) - 1 - i) * 1.6 + 0.3
        ax.add_patch(FancyBboxPatch((2, y), 6, 1.0, boxstyle="round,pad=0.05,rounding_size=0.15",
                                    fc="white", ec=VERDE if i in (2, 3) else "black", lw=1.4))
        ax.text(5, y + 0.5, p, ha="center", va="center", fontsize=11)
        if i < len(pasos) - 1:
            ax.annotate("", xy=(5, y - 0.55), xytext=(5, y - 0.02),
                        arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2))
    fig.savefig(F / "flujo.png"); plt.close(fig)


def leer(p):
    r = [{k.strip(): v for k, v in x.items()} for x in csv.DictReader(open(p))]
    return [int(x["epoch"]) for x in r], [float(x["metrics/mAP50(B)"]) for x in r], [float(x["metrics/mAP50-95(B)"]) for x in r]


def curvas():
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
    for ax, (t, p) in zip(axs, [("Modelo de hojas", S / "hojas_run/results.csv"),
                                ("Modelo de frutos", Path("D:/AppWebPlagasPaltaHass/frutos-entrenamiento/frutos_preciso/results.csv"))]):
        e, a, b = leer(p)
        ax.plot(e, a, color=VERDE, lw=1.4, label="mAP50")
        ax.plot(e, b, color=GRIS, lw=1.4, ls="--", label="mAP50-95")
        ax.axhline(0.70, color="black", lw=0.8, ls=":")
        ax.text(e[-1], 0.705, "umbral 70 %", ha="right", va="bottom", fontsize=9)
        ax.set_title(t, fontsize=11); ax.set_xlabel("Época"); ax.set_ylim(0, 1)
    axs[0].set_ylabel("Valor de la métrica (validación)")
    axs[0].legend(frameon=False, loc="lower right")
    fig.tight_layout(); fig.savefig(F / "curvas.png"); plt.close(fig)


def recall_clase():
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.2), gridspec_kw={"width_ratios": [6, 4]})
    for ax, n in zip(axs, ["frutos", "hojas"]):
        d = json.loads((S / f"eval_{n}.json").read_text(encoding="utf8"))["por_clase"]
        ks = list(d)
        ax.bar(range(len(ks)), [d[k]["R"] * 100 for k in ks],
               color=[GRIS if k.endswith("sana") or k.endswith("sano") else VERDE for k in ks])
        ax.set_xticks(range(len(ks))); ax.set_xticklabels([ETQ[k] for k in ks], rotation=35, ha="right", fontsize=9)
        ax.axhline(70, color="black", lw=0.8, ls=":")
        ax.set_ylim(0, 100); ax.set_title("Modelo de " + n, fontsize=11)
        for i, k in enumerate(ks):
            ax.text(i, d[k]["R"] * 100 + 1.5, f"{d[k]['R'] * 100:.1f}", ha="center", fontsize=8.5)
    axs[0].set_ylabel("Sensibilidad (recall, %)")
    fig.tight_layout(); fig.savefig(F / "recall.png"); plt.close(fig)


def tamano():
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    w = 0.38
    for j, n in enumerate(["frutos", "hojas"]):
        d = json.loads((S / f"eval_{n}.json").read_text(encoding="utf8"))["sensibilidad_por_tamano"]
        ks = list(d)
        v = [d[k]["tasa"][0] * 100 for k in ks]
        ax.bar([i + (j - 0.5) * w for i in range(len(ks))], v, w, color=[VERDE, GRIS][j], label=f"Modelo de {n}")
        for i, x in enumerate(v):
            ax.text(i + (j - 0.5) * w, x + 1.5, f"{x:.1f}", ha="center", fontsize=8.5)
    ax.set_xticks(range(len(ks))); ax.set_xticklabels(["Pequeña (< 2 %)", "Mediana (2–10 %)", "Grande (> 10 %)"])
    ax.set_xlabel("Tamaño de la lesión respecto del área de la imagen"); ax.set_ylabel("Lesiones detectadas (%)")
    ax.set_ylim(0, 100); ax.legend(frameon=False, loc="upper left")
    fig.tight_layout(); fig.savefig(F / "tamano.png"); plt.close(fig)


if __name__ == "__main__":
    flujo(); curvas(); recall_clase(); tamano()
    print(sorted(p.name for p in F.iterdir()))
