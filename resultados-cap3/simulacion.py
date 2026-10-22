"""Simulacion DECLARADA de las mediciones pre/post en los 100 arboles (50 sector A, 50 sector B).

Los valores son resultados esperados para la tesina; en la tesis se reemplazan por las fichas de campo.
Supuestos (documentados en el Cap. III):
- Inspeccion manual por arbol: ~7 min (revision visual de 5 hojas y 5 frutos); con el sistema: ~4.3 min
  (captura de 5 hojas y 5 frutos y lectura del diagnostico). Cada arbol tiene un factor de dificultad
  comun a ambas mediciones (follaje denso, altura), por eso las mediciones son pareadas.
- Tiempo hasta el diagnostico: manual = espera de la visita del tecnico (media ~46 h);
  con el sistema = diagnostico inmediato + confirmacion remota del tecnico (media ~4 h).
- Descarte: 60 frutos evaluados por arbol; descarte fitosanitario esperado 14.5 % (A) y 16 % (B) antes,
  con reduccion relativa ~27 % por deteccion temprana (coherente con tasas de deteccion de 70-97 %).
- Rendimiento 24 kg/arbol; diferencia de precio exportacion - mercado local = S/ 3.80 por kg.
"""
import json
from pathlib import Path
import numpy as np
from scipy import stats

S = Path(__file__).parent
rng = np.random.default_rng(2026)
N_A = N_B = 50
n = N_A + N_B
sector = np.array(["A"] * N_A + ["B"] * N_B)
codigo = [f"{s}-{i + 1:02d}" for s, i in zip(sector, list(range(N_A)) + list(range(N_B)))]

# ---- tiempo de inspeccion por arbol (min)
dif = rng.lognormal(0, 0.22, n) * np.where(sector == "B", 1.06, 1.0)
t_pre = 7.0 * dif * rng.lognormal(0, 0.12, n)
t_post = 4.3 * dif ** 0.8 * rng.lognormal(0, 0.15, n)
t_pre, t_post = np.round(t_pre, 1), np.round(t_post, 1)

# ---- tiempo desde la deteccion del sintoma hasta el diagnostico (h)
r_pre = np.round(rng.gamma(3.2, 46 / 3.2, n), 1)
r_post = np.round(rng.lognormal(np.log(3.2), 0.6, n), 1)

# ---- descarte (frutos evaluados = 60 por arbol)
F = 60
base = np.where(sector == "A", 0.145, 0.160)
p_pre = rng.beta(base * 40, (1 - base) * 40)
p_post = np.clip(p_pre * rng.normal(0.73, 0.12, n), 0, 1)
d_pre = rng.binomial(F, p_pre)
d_post = rng.binomial(F, p_post)
kg = rng.normal(24, 4, n).clip(12)
PRECIO = 3.80
loss_pre = np.round(kg * d_pre / F * PRECIO, 2)
loss_post = np.round(kg * d_post / F * PRECIO, 2)


def contraste(pre, post, nombre):
    d = pre - post
    w, p_sw = stats.shapiro(d)
    if p_sw < 0.05:
        r = stats.wilcoxon(pre, post, alternative="greater")
        prueba, est, p = "Wilcoxon", float(r.statistic), float(r.pvalue)
        z = stats.norm.isf(p)
        efecto = ("r", z / np.sqrt(len(d)))
    else:
        r = stats.ttest_rel(pre, post, alternative="greater")
        prueba, est, p = "t de Student pareada", float(r.statistic), float(r.pvalue)
        efecto = ("d de Cohen", d.mean() / d.std(ddof=1))
    out = dict(variable=nombre, media_pre=float(pre.mean()), de_pre=float(pre.std(ddof=1)),
               media_post=float(post.mean()), de_post=float(post.std(ddof=1)), dif=float(d.mean()),
               reduccion=float(d.mean() / pre.mean()), shapiro_W=float(w), shapiro_p=float(p_sw),
               prueba=prueba, estadistico=est, p=p, efecto=efecto[0], efecto_valor=float(efecto[1]))
    print(json.dumps(out, ensure_ascii=False))
    return out


pct_pre, pct_post = d_pre / F * 100, d_post / F * 100
res = {
    "tiempo_arbol": contraste(t_pre, t_post, "Tiempo de inspección por árbol (min)"),
    "tiempo_respuesta": contraste(r_pre, r_post, "Tiempo hasta el diagnóstico (h)"),
    "descarte": contraste(pct_pre, pct_post, "Frutos descartados (%)"),
    "perdida": contraste(loss_pre, loss_post, "Pérdida económica por árbol (S/)"),
    "totales": dict(frutos=int(F * n), desc_pre=int(d_pre.sum()), desc_post=int(d_post.sum()),
                    perdida_pre=float(loss_pre.sum()), perdida_post=float(loss_post.sum()),
                    ha_pre_h=float(t_pre.mean() * 625 / 60), ha_post_h=float(t_post.mean() * 625 / 60)),
}
(S / "sim_resultados.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf8")

# ---- Excel con los datos simulados (plantilla para reemplazar por campo)
from openpyxl import Workbook
wb = Workbook(); ws = wb.active; ws.title = "datos_simulados"
ws.append(["Código", "Sector", "Tiempo pre (min)", "Tiempo post (min)", "Respuesta pre (h)", "Respuesta post (h)",
           "Frutos evaluados", "Descartados pre", "Descartados post", "Pérdida pre (S/)", "Pérdida post (S/)"])
for i in range(n):
    ws.append([codigo[i], sector[i], float(t_pre[i]), float(t_post[i]), float(r_pre[i]), float(r_post[i]), F,
               int(d_pre[i]), int(d_post[i]), float(loss_pre[i]), float(loss_post[i])])
ws2 = wb.create_sheet("nota")
ws2.append(["DATOS SIMULADOS para la tesina (resultados esperados). Reemplazar por las fichas de campo en la tesis."])
wb.save(S / "datos_simulados_campo.xlsx")
print(json.dumps(res["totales"]))
