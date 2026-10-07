"""Definiciones compartidas: clases originales, mapeo a hojas/frutos y lectura de etiquetas YOLO."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "DatasetOriginal"
REVISION = RAIZ / "revision"
SPLITS = ("train", "valid", "test")

CLASES_ORIGINALES = [
    "Anthracnose", "Healthy", "Pest Infested", "Pest attack", "Stem End Rot",
    "algal_leaf_spot", "anthracnose", "cercospora_spot", "healthy", "nutrient_deficiency",
    "persea_mite", "powdery_mildew", "scab", "stem end rot", "sunblotch",
]

CLASES = {
    "hojas": ["hoja_sana", "antracnosis_hoja", "plaga", "deficiencia_nutricional"],
    "frutos": ["fruto_sano", "antracnosis_fruto", "cercospora", "rona", "pudricion_peduncular", "sunblotch"],
}

# Clase original -> (organo, clase nueva). En 'Anthracnose' y 'Healthy' el organo depende
# del tipo de anotacion: poligono = hoja, caja = fruto (verificado visualmente).
# None = clase descartada.
_MAPEO = {
    "Anthracnose": {"poly": ("hojas", "antracnosis_hoja"), "box": ("frutos", "antracnosis_fruto")},
    "Healthy": {"poly": ("hojas", "hoja_sana"), "box": ("frutos", "fruto_sano")},
    "Pest Infested": ("hojas", "plaga"),
    "Pest attack": None,          # lesiones pequenas: criterio distinto a 'Pest Infested' (hoja completa)
    "Stem End Rot": ("frutos", "pudricion_peduncular"),
    "algal_leaf_spot": None,      # muy pocas anotaciones
    "anthracnose": ("frutos", "antracnosis_fruto"),
    "cercospora_spot": ("frutos", "cercospora"),
    "healthy": ("frutos", "fruto_sano"),
    "nutrient_deficiency": ("hojas", "deficiencia_nutricional"),
    "persea_mite": None,          # muy pocas anotaciones
    "powdery_mildew": None,       # muy pocas anotaciones
    "scab": ("frutos", "rona"),
    "stem end rot": ("frutos", "pudricion_peduncular"),
    "sunblotch": ("frutos", "sunblotch"),
}


def mapear(clase_original, es_poligono):
    """Devuelve (organo, clase_nueva) o None si la anotacion se descarta."""
    m = _MAPEO[CLASES_ORIGINALES[clase_original]]
    if isinstance(m, dict):
        return m["poly" if es_poligono else "box"]
    return m


def leer_anotaciones(ruta_label):
    """Lee un .txt YOLO (cajas o poligonos) y devuelve cada anotacion como caja (xc, yc, w, h)."""
    anotaciones = []
    for linea in ruta_label.read_text().splitlines():
        t = linea.split()
        if not t:
            continue
        c, v = int(t[0]), [float(x) for x in t[1:]]
        es_poligono = len(v) > 4
        if es_poligono:
            xs = [min(max(x, 0.0), 1.0) for x in v[0::2]]
            ys = [min(max(y, 0.0), 1.0) for y in v[1::2]]
            x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
            caja = ((x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1)
        else:
            caja = tuple(v)
        if caja[2] < 1e-4 or caja[3] < 1e-4:
            continue
        anotaciones.append({"clase": c, "poligono": es_poligono, "caja": caja})
    return anotaciones


def cargar_imagenes():
    """Lista de imagenes del dataset original con sus anotaciones. id = 'split/nombre_sin_extension'."""
    imagenes = []
    for split in SPLITS:
        for ruta_img in sorted((ORIGEN / split / "images").iterdir()):
            ruta_label = ORIGEN / split / "labels" / (ruta_img.stem + ".txt")
            imagenes.append({
                "id": f"{split}/{ruta_img.stem}",
                "split": split,
                "imagen": ruta_img,
                "anotaciones": leer_anotaciones(ruta_label) if ruta_label.exists() else [],
            })
    return imagenes


def anotaciones_de_organo(imagen, organo):
    """Anotaciones de la imagen que pertenecen al organo, como (indice_clase_nueva, caja)."""
    resultado = []
    for a in imagen["anotaciones"]:
        m = mapear(a["clase"], a["poligono"])
        if m and m[0] == organo:
            resultado.append((CLASES[organo].index(m[1]), a["caja"]))
    return resultado
