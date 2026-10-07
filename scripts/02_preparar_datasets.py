"""Construye DatasetHojas/ y DatasetFrutos/ a partir de DatasetOriginal/.

Pasos:
  1. Remapea las 15 clases originales a clases por organo (ver comun.py) y convierte poligonos a cajas.
  2. Quita del dataset de frutos las imagenes listadas en revision/excluir_fruto_sano.txt.
  3. Detecta duplicados exactos (se deja una sola copia) y casi-duplicados (rafagas, misma foto
     con otro nombre), y los agrupa para que un grupo nunca quede repartido entre splits (evita fuga).
  4. Divide train/valid/test (70/20/10 por defecto) por grupos, estratificando por clase.

Uso:
  python scripts/02_preparar_datasets.py                 # requiere revision/excluir_fruto_sano.txt
  python scripts/02_preparar_datasets.py --sin-revision  # genera sin filtrar fruto_sano (provisional)
"""
import argparse
import json
import random
import re
import shutil
from collections import Counter, defaultdict

import numpy as np
from PIL import Image

from comun import CLASES, RAIZ, REVISION, SPLITS, anotaciones_de_organo, cargar_imagenes

SALIDAS = {"hojas": RAIZ / "DatasetHojas", "frutos": RAIZ / "DatasetFrutos"}
MARCA = ".generado_por_preparar_datasets"

# Umbrales calibrados mirando pares de imagenes (ver ESTRATEGIA_DATASET.md):
# dHash de 256 bits + diferencia media de color ignorando fondo blanco/negro (escala 0-255).
DHASH_MAX = 16
COLOR_CASI_DUPLICADO = 10.0   # por debajo: misma escena (rafaga, recorte, re-subida)
COLOR_DUPLICADO = 1.5         # junto con dHash 0: la misma imagen


def firmas(imagenes):
    hashes, colores = [], []
    for im in imagenes:
        img = Image.open(im["imagen"])
        p = np.asarray(img.convert("L").resize((17, 16), Image.BILINEAR), dtype=np.int16)
        bits = (p[:, :-1] > p[:, 1:]).flatten()
        hashes.append(int("".join("1" if b else "0" for b in bits), 2))
        colores.append(np.asarray(img.convert("RGB").resize((32, 32), Image.BILINEAR), dtype=np.float32))
    colores = np.stack(colores)
    fondo = (colores.min(-1) > 225) | (colores.max(-1) < 25)
    return hashes, colores, fondo


def nombre_original(ruta):
    """Nombre de la foto antes de que Roboflow le agregara '_jpg.rf.<hash>'."""
    return ruta.stem.split(".rf.")[0].rsplit("_", 1)[0].lower()


def fruto_giratorio(ruta):
    """Serie de mesa giratoria 'P10_20-degrees': devuelve 'P10' (cada fruto es su propio grupo)."""
    m = re.match(r"(P\d+)_\d+-degrees", ruta.name)
    return m.group(1) if m else None


class Grupos:
    def __init__(self, n):
        self.padre = list(range(n))

    def raiz(self, i):
        while self.padre[i] != i:
            self.padre[i] = self.padre[self.padre[i]]
            i = self.padre[i]
        return i

    def unir(self, a, b):
        self.padre[self.raiz(a)] = self.raiz(b)


def agrupar(imagenes):
    """Devuelve (grupo por imagen, conjunto de indices que son copias exactas a descartar)."""
    n = len(imagenes)
    hashes, colores, fondo = firmas(imagenes)
    grupos = Grupos(n)
    copias = []

    por_nombre = defaultdict(list)
    for i, im in enumerate(imagenes):
        por_nombre[nombre_original(im["imagen"])].append(i)
    giratorio = [fruto_giratorio(im["imagen"]) for im in imagenes]
    for i, clave in enumerate(giratorio):
        if clave:
            por_nombre["giratorio:" + clave].append(i)
    for idx in por_nombre.values():
        for j in idx[1:]:
            grupos.unir(idx[0], j)

    for i in range(n):
        for j in range(i + 1, n):
            if giratorio[i] and giratorio[j]:
                continue   # mismo fondo gris: el hash los confunde; ya estan agrupados por nombre
            d = (hashes[i] ^ hashes[j]).bit_count()
            if d > DHASH_MAX:
                continue
            mascara = ~(fondo[i] & fondo[j])
            dif = float(np.abs(colores[i] - colores[j]).mean(-1)[mascara].mean()) if mascara.any() else 0.0
            if dif < COLOR_CASI_DUPLICADO:
                grupos.unir(i, j)
                if d == 0 and dif < COLOR_DUPLICADO:
                    copias.append((i, j))

    # De cada par de copias exactas se descarta la que tiene menos anotaciones.
    descartar = set()
    for i, j in copias:
        if i in descartar or j in descartar:
            continue
        descartar.add(i if len(imagenes[i]["anotaciones"]) < len(imagenes[j]["anotaciones"]) else j)
    return [grupos.raiz(i) for i in range(n)], descartar


def dividir(muestras, n_clases, proporciones, semilla):
    """Asigna grupos completos a splits buscando que cada clase quede cerca de la proporcion objetivo."""
    por_grupo = defaultdict(list)
    for m in muestras:
        por_grupo[m["grupo"]].append(m)
    grupos = list(por_grupo.values())
    random.Random(semilla).shuffle(grupos)

    total = np.zeros(n_clases)
    vectores = []
    for g in grupos:
        v = np.zeros(n_clases)
        for m in g:
            for c, _ in m["cajas"]:
                v[c] += 1
        vectores.append(v)
        total += v
    n_imgs = len(muestras)
    objetivo = np.outer(proporciones, total)
    objetivo_imgs = np.array(proporciones) * n_imgs
    actual = np.zeros_like(objetivo)
    actual_imgs = np.zeros(len(proporciones))

    # Primero los grupos con las clases mas escasas, luego los mas grandes.
    rareza = [min(total[c] for c in np.nonzero(v)[0]) for v in vectores]
    orden = sorted(range(len(grupos)), key=lambda k: (rareza[k], -len(grupos[k])))
    asignacion = {}
    for k in orden:
        v = vectores[k]
        clases = np.nonzero(v)[0]
        mejor, mejor_puntaje = 0, None
        for s in range(len(proporciones)):
            falta_clases = ((objetivo[s, clases] - actual[s, clases]) / np.maximum(total[clases], 1)).sum()
            falta_imgs = (objetivo_imgs[s] - actual_imgs[s]) / n_imgs
            puntaje = (falta_clases, falta_imgs)
            if mejor_puntaje is None or puntaje > mejor_puntaje:
                mejor, mejor_puntaje = s, puntaje
        actual[mejor] += v
        actual_imgs[mejor] += len(grupos[k])
        for m in grupos[k]:
            asignacion[m["id"]] = SPLITS[mejor]
    return asignacion


def escribir(organo, muestras, asignacion):
    salida = SALIDAS[organo]
    if salida.exists():
        if not (salida / MARCA).exists():
            raise SystemExit(f"{salida} existe y no fue generado por este script; no se sobrescribe.")
        shutil.rmtree(salida)
    for s in SPLITS:
        (salida / s / "images").mkdir(parents=True)
        (salida / s / "labels").mkdir(parents=True)
    (salida / MARCA).write_text("Carpeta generada por scripts/02_preparar_datasets.py; se borra al regenerar.\n")

    for m in muestras:
        s = asignacion[m["id"]]
        destino = salida / s / "images" / m["imagen"].name
        if destino.exists():
            raise SystemExit(f"Nombre de imagen repetido: {destino.name}")
        shutil.copy2(m["imagen"], destino)
        lineas = [f"{c} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}" for c, (xc, yc, w, h) in m["cajas"]]
        (salida / s / "labels" / (m["imagen"].stem + ".txt")).write_text("\n".join(lineas) + "\n")

    nombres = CLASES[organo]
    yaml = [f"# Generado por scripts/02_preparar_datasets.py. En Colab/otra PC cambia 'path' a la ubicacion real.",
            f"path: {salida.as_posix()}",
            "train: train/images", "val: valid/images", "test: test/images", "",
            f"nc: {len(nombres)}", "names:"] + [f"  {i}: {n}" for i, n in enumerate(nombres)]
    (salida / "data.yaml").write_text("\n".join(yaml) + "\n", encoding="utf-8")


def resumen(organo, muestras, asignacion):
    cajas = defaultdict(Counter)
    imgs = defaultdict(Counter)
    for m in muestras:
        s = asignacion[m["id"]]
        for c in {c for c, _ in m["cajas"]}:
            imgs[c][s] += 1
        for c, _ in m["cajas"]:
            cajas[c][s] += 1
    filas = []
    for c, nombre in enumerate(CLASES[organo]):
        t = sum(cajas[c].values())
        filas.append({"clase": nombre, **{f"cajas_{s}": cajas[c][s] for s in SPLITS},
                      **{f"imagenes_{s}": imgs[c][s] for s in SPLITS},
                      "porcentaje": "/".join(f"{100 * cajas[c][s] / max(t, 1):.0f}" for s in SPLITS)})
    total_imgs = Counter(asignacion[m["id"]] for m in muestras)
    return {"imagenes": {s: total_imgs[s] for s in SPLITS}, "grupos": len({m["grupo"] for m in muestras}),
            "clases": filas}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-revision", action="store_true", help="no exige revision/excluir_fruto_sano.txt")
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--proporciones", type=float, nargs=3, default=[0.7, 0.2, 0.1], metavar=("TRAIN", "VALID", "TEST"))
    args = ap.parse_args()

    ruta_excluir = REVISION / "excluir_fruto_sano.txt"
    if ruta_excluir.exists():
        excluir = {l.strip() for l in ruta_excluir.read_text(encoding="utf-8").splitlines() if l.strip()}
    elif args.sin_revision:
        excluir = set()
        print("AVISO: sin revision/excluir_fruto_sano.txt; 'fruto_sano' incluye fruta oscura y clipart.")
    else:
        raise SystemExit("Falta revision/excluir_fruto_sano.txt (genera la galeria con 01_galeria_fruto_sano.py) "
                         "o usa --sin-revision.")

    imagenes = cargar_imagenes()
    print(f"{len(imagenes)} imagenes originales. Buscando duplicados...")
    grupo, descartar = agrupar(imagenes)

    reporte = {"semilla": args.semilla, "proporciones": args.proporciones,
               "copias_exactas_descartadas": sorted(imagenes[i]["id"] for i in descartar),
               "excluidas_fruto_sano": len(excluir), "excluidas_completas": 0, "excluidas_solo_fruto_sano": 0}
    sano = CLASES["frutos"].index("fruto_sano")
    for organo in ("hojas", "frutos"):
        muestras = []
        for i, im in enumerate(imagenes):
            if i in descartar:
                continue
            cajas = anotaciones_de_organo(im, organo)
            if organo == "frutos" and im["id"] in excluir:
                # La exclusion solo afecta a 'fruto_sano': si la imagen tiene frutos con otras
                # enfermedades, se conserva con esas etiquetas. Si solo tenia fruto_sano, sale completa.
                cajas = [(c, caja) for c, caja in cajas if c != sano]
                reporte["excluidas_completas" if not cajas else "excluidas_solo_fruto_sano"] += 1
            if cajas:
                muestras.append({**im, "cajas": cajas, "grupo": grupo[i]})
        asignacion = dividir(muestras, len(CLASES[organo]), args.proporciones, args.semilla)
        escribir(organo, muestras, asignacion)
        reporte[organo] = resumen(organo, muestras, asignacion)

        r = reporte[organo]
        print(f"\n== {SALIDAS[organo].name}: {sum(r['imagenes'].values())} imagenes en {r['grupos']} grupos "
              f"| train {r['imagenes']['train']} / valid {r['imagenes']['valid']} / test {r['imagenes']['test']}")
        print(f"{'clase':24s} {'train':>6s} {'valid':>6s} {'test':>6s}   % cajas")
        for f in r["clases"]:
            print(f"{f['clase']:24s} {f['cajas_train']:6d} {f['cajas_valid']:6d} {f['cajas_test']:6d}   {f['porcentaje']}")

    REVISION.mkdir(exist_ok=True)
    (REVISION / "reporte_preparacion.json").write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nExcluidas en la revision: {reporte['excluidas_completas']} imagenes completas (solo tenian fruto_sano), "
          f"{reporte['excluidas_solo_fruto_sano']} conservadas sin sus cajas de fruto_sano (tenian otras enfermedades).")
    print(f"Copias exactas descartadas: {len(descartar)}. Reporte: revision/reporte_preparacion.json")


if __name__ == "__main__":
    main()
