"""Reemplaza la plantilla del Cap. III (tesis de referencia) por los resultados de la tesis de palta Hass."""
import json, re, sys
from pathlib import Path

S = Path(__file__).parent
sys.path.insert(0, str(S))
from docxlib import parrafo, subtitulo, nota, leyenda, tabla, Imagenes

U = S / "work/v4"
DOC = U / "word/document.xml"
FR = json.loads((S / "eval_frutos.json").read_text(encoding="utf8"))
HO = json.loads((S / "eval_hojas.json").read_text(encoding="utf8"))
RT = json.loads((S / "eval_hojas_rt.json").read_text(encoding="utf8"))


def binom_p(k, n, p0):
    """p unilateral exacto P(X >= k | n, p0)."""
    from math import comb
    return sum(comb(n, i) * p0 ** i * (1 - p0) ** (n - i) for i in range(k, n + 1))


fp = lambda v: "< 0.001" if v < 0.001 else f"{v:.3f}"

pct = lambda v, d=1: f"{v * 100:.{d}f}".replace(".", ".") + " %"
num = lambda v, d=1: f"{v * 100:.{d}f}"
ic = lambda t: f"{num(t[1])} – {num(t[2])}"
ETQ = {"fruto_sano": "Fruto sano", "antracnosis_fruto": "Antracnosis en fruto", "cercospora": "Cercospora",
       "rona": "Roña", "pudricion_peduncular": "Pudrición peduncular", "sunblotch": "Sunblotch",
       "hoja_sana": "Hoja sana", "antracnosis_hoja": "Antracnosis en hoja", "plaga": "Plagas (trips/ácaros)",
       "deficiencia_nutricional": "Deficiencia nutricional"}


def nivel(m):
    return "Alto" if m >= 0.85 else "Aceptable" if m >= 0.70 else "Bajo"


img = Imagenes(U)
T = iter(range(3, 40))   # Cap. II: Tablas 1 y 2
F = iter(range(2, 40))   # Cap. II termina en la Figura 1
x = []
add = x.append
fg, hj, rg = FR["global"], HO["global"], RT["global"]
fi, hi, ri = FR["imagen"], HO["imagen"], RT["imagen"]

# ---------------------------------------------------------------- introduccion
add(parrafo(
    "En este capítulo se presentaron los resultados obtenidos tras el desarrollo y la evaluación del sistema de visión "
    "computacional para el diagnóstico fitosanitario de la palta Hass. Los resultados se organizaron en función de los tres "
    "objetivos específicos de la investigación: la precisión en el diagnóstico fitosanitario, el tiempo de inspección y la "
    "disminución de las pérdidas por descarte, esta última abordada a partir de la capacidad del sistema para detectar de "
    "forma temprana las enfermedades del fruto y de la hoja. El sistema implementado siguió el flujo de procesamiento que se "
    "muestra en la Figura 2."))
n = next(F)
add(leyenda("Figura", n, "Diagrama de flujo del proceso del sistema de visión computacional"))
add(img.drawing(S / "fig/flujo.png", 9.5, "Diagrama de flujo del sistema"))
add(nota("Elaboración propia. El umbral de confianza de 0.35 corresponde a la configuración del servidor de inferencia."))
add(parrafo(
    "Como se observa en la Figura 2, el usuario capturó la imagen desde la aplicación web, seleccionó el órgano a evaluar "
    "(hoja o fruto) y el sistema la procesó con el modelo YOLO11s correspondiente; en el modo de tiempo real, las hojas se "
    "analizaron directamente en el navegador con un modelo ligero YOLO11n. Las detecciones con una confianza igual o "
    "superior a 0.35 se tradujeron en un veredicto (sano o con alerta fitosanitaria), acompañado de acciones recomendadas, y "
    "cada inspección quedó registrada en el historial del sistema, desde donde pudo exportarse como reporte en formato PDF. "
    "Los indicadores evaluados para cada objetivo se resumen en la Tabla 3."))

t = next(T)
add(leyenda("Tabla", t, "Objetivos, dimensiones e indicadores evaluados"))
add(tabla(["Objetivo específico", "Dimensión", "Indicadores", "Fuente de datos"], [
    ["OE1. Precisión en el diagnóstico fitosanitario", "Precisión diagnóstica",
     "P, R, F1, mAP50, mAP50-95; sensibilidad, especificidad, exactitud y κ por imagen",
     "Split de prueba del dataset (618 imágenes) y registros del sistema"],
    ["OE2. Tiempo de inspección", "Tiempo de inspección",
     "Tiempo de procesamiento por imagen (ms); tiempo promedio por árbol (min)",
     "Medición en el split de prueba; [[fichas de campo (pendiente)]]"],
    ["OE3. Pérdidas por descarte", "Pérdidas por descarte (detección temprana)",
     "Tasa de detección por enfermedad; sensibilidad según tamaño de lesión; % de frutos descartados",
     "Split de prueba del dataset; [[fichas de campo (pendiente)]]"],
], [2300, 1700, 2900, 2000], ["left", "left", "left", "left"]))
add(nota("Elaboración propia. P = precisión; R = sensibilidad (recall); F1 = media armónica de P y R; mAP = precisión media "
         "promedio; κ = coeficiente kappa de Cohen."))

# ---------------------------------------------------------------- datos y entrenamiento
add(subtitulo("Conjunto de datos y entrenamiento de los modelos"))
add(parrafo(
    "Los modelos se entrenaron con imágenes del repositorio público Roboflow Universe, depuradas mediante eliminación de "
    "duplicados y control de fuga de información entre particiones, y divididas en entrenamiento, validación y prueba. Se "
    "entrenó un modelo independiente para cada órgano: el modelo de hojas, con cuatro clases, y el modelo de frutos, con seis "
    "clases. La composición de cada conjunto se presenta en la Tabla 4."))
t = next(T)
add(leyenda("Tabla", t, "Composición del conjunto de datos por modelo y partición"))
add(tabla(["Modelo", "Clases", "Entrenamiento", "Validación", "Prueba", "Instancias en prueba"], [
    ["Hojas", "4", "1,657", "486", "237", "276"],
    ["Frutos", "6", "2,545", "790", "381", "535"],
    ["Total", "10", "4,202", "1,276", "618", "811"],
], [1300, 900, 1500, 1300, 1100, 1900], total=True))
add(nota("Elaboración propia. Las instancias corresponden a las cajas delimitadoras etiquetadas en las imágenes de prueba. "
         "Clases del modelo de hojas: hoja sana, antracnosis, plagas (trips/ácaros) y deficiencia nutricional. Clases del modelo "
         "de frutos: fruto sano, antracnosis, cercospora, roña, pudrición peduncular y sunblotch."))

add(parrafo(
    "Los modelos que procesan las imágenes en el servidor se entrenaron con la arquitectura YOLO11s y una resolución de "
    "entrada de 1024 píxeles. En el caso de las hojas, además, se entrenó una variante ligera YOLO11n de 640 píxeles "
    "destinada al modo de inspección en tiempo real, en el que la inferencia se ejecuta en el navegador del dispositivo "
    "móvil y se prioriza la velocidad de respuesta. El modelo de hojas del servidor se obtuvo continuando el entrenamiento "
    "a partir de los pesos de una corrida previa durante 100 épocas adicionales. La configuración empleada se detalla en "
    "la Tabla 5."))
t = next(T)
add(leyenda("Tabla", t, "Configuración del entrenamiento de los modelos"))
add(tabla(["Parámetro", "Hojas (servidor)", "Hojas (tiempo real)", "Frutos (servidor)"], [
    ["Arquitectura base", "YOLO11s", "YOLO11n", "YOLO11s (preentrenado)"],
    ["Punto de partida", "Pesos de un entrenamiento previo", "Pesos preentrenados", "Pesos preentrenados"],
    ["Resolución de entrada", "1024 px", "640 px", "1024 px"],
    ["Épocas programadas / ejecutadas", "100 / 100", "180 / 179", "200 / 109"],
    ["Paciencia (parada temprana)", "40 épocas", "40 épocas", "40 épocas"],
    ["Tamaño de lote", "8", "32", "8"],
    ["Optimizador y tasa inicial", "AdamW, 0.00125", "Automático, 0.01", "Automático, 0.01"],
    ["Programación de la tasa", "Coseno", "Coseno", "Coseno"],
    ["Mejor época (validación)", "97", "139", "93"],
    ["mAP50 en validación (mejor época)", pct(0.92145), pct(0.90728), pct(0.78683)],
    ["mAP50-95 en validación (mejor época)", pct(0.80154), pct(0.84644), pct(0.59137)],
], [2900, 1900, 1900, 1900]))
add(nota("Elaboración propia a partir de los archivos args.yaml y results.csv generados por Ultralytics durante el entrenamiento."))
n = next(F)
add(parrafo(f"La Figura {n} muestra la evolución de las métricas mAP50 y mAP50-95 en el conjunto de validación durante el "
            "entrenamiento. En los tres modelos la curva de mAP50 superó el umbral del 70 % y se estabilizó en las últimas "
            "épocas, lo que indicó que el entrenamiento convergió sin evidencias de sobreajuste severo. Los modelos de hojas "
            "superaron el umbral antes de la décima época y se estabilizaron por encima del 90 % de mAP50; el modelo ligero "
            "finalizó por parada temprana en la época 179, al no mejorar durante 40 épocas consecutivas desde la época 139. "
            "El modelo de frutos requirió alrededor de 25 épocas para superar el umbral y se estabilizó cerca del 78 %, lo "
            "que reflejó la mayor dificultad de esta tarea, con seis clases y lesiones de menor contraste sobre la cáscara "
            "oscura del fruto."))
add(leyenda("Figura", n, "Evolución de mAP50 y mAP50-95 durante el entrenamiento"))
add(img.drawing(S / "fig/curvas.png", 16.0, "Curvas de entrenamiento"))
add(nota("Elaboración propia. La línea punteada representa el umbral mínimo de desempeño (mAP50 = 70 %) establecido en la "
         "hipótesis específica 1."))

# ---------------------------------------------------------------- OE1
add(subtitulo("Resultados del objetivo específico 1: precisión en el diagnóstico fitosanitario"))
add(parrafo(
    "Para determinar la precisión del diagnóstico, los tres modelos se evaluaron sobre el conjunto de prueba, conformado por "
    "imágenes que no participaron en el entrenamiento ni en la selección del modelo. Los resultados globales se presentan "
    "en la Tabla 6, junto con el nivel alcanzado según la escala definida en la matriz de operacionalización (alto si "
    "mAP50 ≥ 85 %, aceptable entre 70 % y 84 %, y bajo si es menor de 70 %)."))
t = next(T)
add(leyenda("Tabla", t, "Desempeño global de los modelos en el conjunto de prueba"))
add(tabla(["Modelo", "Precisión (P)", "Recall (R)", "F1-score", "mAP50", "mAP50-95", "Nivel"], [
    ["Hojas (servidor)", pct(hj["P"]), pct(hj["R"]), pct(hj["F1"]), pct(hj["mAP50"]), pct(hj["mAP50_95"]), nivel(hj["mAP50"])],
    ["Hojas (tiempo real)", pct(rg["P"]), pct(rg["R"]), pct(rg["F1"]), pct(rg["mAP50"]), pct(rg["mAP50_95"]), nivel(rg["mAP50"])],
    ["Frutos (servidor)", pct(fg["P"]), pct(fg["R"]), pct(fg["F1"]), pct(fg["mAP50"]), pct(fg["mAP50_95"]), nivel(fg["mAP50"])],
], [1900, 1150, 1100, 1100, 1100, 1200, 1150]))
add(nota("Elaboración propia. Evaluación con Ultralytics sobre el split de prueba (237 imágenes de hojas y 381 de frutos), "
         "con umbral de IoU de 0.50 para mAP50. Los modelos del servidor se evaluaron a 1024 px y el modelo de tiempo real "
         "a 640 px."))
add(parrafo(
    f"Como se aprecia en la Tabla 6, el modelo de hojas del servidor alcanzó un mAP50 de {pct(hj['mAP50'])} y un F1-score "
    f"de {pct(hj['F1'])}, y el modelo ligero de tiempo real obtuvo un mAP50 de {pct(rg['mAP50'])} y un F1-score de "
    f"{pct(rg['F1'])}; ambos se ubicaron en el nivel alto. El modelo de frutos obtuvo un mAP50 de {pct(fg['mAP50'])} y un "
    f"F1-score de {pct(fg['F1'])}, en el nivel aceptable. Los tres modelos superaron el umbral mínimo del 70 % planteado en "
    "la hipótesis específica 1. Cabe resaltar que el modelo ligero de hojas igualó e incluso superó ligeramente al modelo "
    f"del servidor, con una precisión mayor ({pct(rg['P'])} frente a {pct(hj['P'])}) y una sensibilidad algo menor "
    f"({pct(rg['R'])} frente a {pct(hj['R'])}), lo que indicó que, para las lesiones foliares del conjunto evaluado, la "
    "resolución de 640 píxeles resultó suficiente. Por su parte, el modelo de frutos presentó una precisión "
    f"({pct(fg['P'])}) superior a su sensibilidad ({pct(fg['R'])}), lo que indicó que sus detecciones fueron "
    "mayoritariamente correctas, aunque omitió una parte de las lesiones presentes. El desempeño por clase se detalla en "
    "la Tabla 7."))
t = next(T)
add(leyenda("Tabla", t, "Desempeño por clase en el conjunto de prueba"))
filas = []
for nom, d in (("Hojas (servidor)", HO), ("Hojas (tiempo real)", RT), ("Frutos (servidor)", FR)):
    for k, v in d["por_clase"].items():
        filas.append([nom, ETQ[k], pct(v["P"]), pct(v["R"]), pct(v["F1"]), pct(v["mAP50"]), pct(v["mAP50_95"])])
add(tabla(["Modelo", "Clase", "P", "R", "F1", "mAP50", "mAP50-95"], filas,
          [1700, 2300, 950, 950, 950, 1000, 1100], ["left", "left"] + ["center"] * 5))
add(nota("Elaboración propia. Resultados por clase del split de prueba."))
pf, ph, pr = FR["por_clase"], HO["por_clase"], RT["por_clase"]
add(parrafo(
    "En el modelo de hojas del servidor, la deficiencia nutricional obtuvo el mejor desempeño (mAP50 = "
    f"{pct(ph['deficiencia_nutricional']['mAP50'])}), seguida de la hoja sana ({pct(ph['hoja_sana']['mAP50'])}) y de la "
    f"antracnosis ({pct(ph['antracnosis_hoja']['mAP50'])}); la clase de plagas registró el valor más bajo "
    f"({pct(ph['plaga']['mAP50'])}) y la menor sensibilidad ({pct(ph['plaga']['R'])}), debido a que los daños por trips y "
    "ácaros son pequeños y se confunden con otras alteraciones de la lámina foliar. El modelo de tiempo real reprodujo el "
    f"mismo patrón, con la deficiencia nutricional en primer lugar ({pct(pr['deficiencia_nutricional']['mAP50'])}) y las "
    f"plagas en el último ({pct(pr['plaga']['mAP50'])}), y superó al modelo del servidor en la antracnosis "
    f"({pct(pr['antracnosis_hoja']['mAP50'])} frente a {pct(ph['antracnosis_hoja']['mAP50'])}). Asimismo, en el modelo del "
    f"servidor la hoja sana registró la precisión más baja ({pct(ph['hoja_sana']['P'])}), lo que reflejó detecciones de "
    "hojas sanas sobre zonas sin etiqueta, un tipo de error que no genera alertas fitosanitarias. En el modelo de frutos, sunblotch "
    f"({pct(pf['sunblotch']['mAP50'])}), cercospora ({pct(pf['cercospora']['mAP50'])}) y pudrición peduncular "
    f"({pct(pf['pudricion_peduncular']['mAP50'])}) superaron el 80 %, mientras que la antracnosis "
    f"({pct(pf['antracnosis_fruto']['mAP50'])}) y el fruto sano ({pct(pf['fruto_sano']['mAP50'])}) presentaron los valores "
    "más bajos, lo cual se asoció a la similitud visual entre las lesiones iniciales de antracnosis, las manchas de roña y "
    "el oscurecimiento natural de la cáscara del fruto Hass maduro."))
CM = json.loads((S / "cm_test.json").read_text(encoding="utf8"))
nh, nr, nf = next(F), next(F), next(F)
add(parrafo(
    f"Para identificar el tipo de error cometido por cada modelo se elaboraron las matrices de confusión de las Figuras {nh} "
    f"a {nf}, calculadas con el mismo umbral de confianza que aplica el sistema desplegado (0.35) y un IoU mínimo de 0.45 "
    "para emparejar cada detección con su etiqueta. Las filas representan la clase real y las columnas la clase predicha; "
    "la columna «No detectado» agrupa las lesiones u órganos que el sistema no localizó y la fila «Fondo» las detecciones "
    "emitidas sobre zonas sin etiqueta (falsos positivos)."))
add(leyenda("Figura", nh, "Matriz de confusión del modelo de hojas del servidor en el conjunto de prueba"))
add(img.drawing(S / "fig/cm_hojas.png", 11.0, "Matriz de confusión del modelo de hojas del servidor"))
add(nota("Elaboración propia. Valores normalizados por fila (clase real) y, entre paréntesis, número de instancias. "
         "Umbral de confianza = 0.35; IoU de emparejamiento = 0.45."))
add(leyenda("Figura", nr, "Matriz de confusión del modelo de hojas de tiempo real en el conjunto de prueba"))
add(img.drawing(S / "fig/cm_hojas_rt.png", 11.0, "Matriz de confusión del modelo de hojas de tiempo real"))
add(nota("Elaboración propia. Valores normalizados por fila (clase real) y, entre paréntesis, número de instancias. "
         "Umbral de confianza = 0.35; IoU de emparejamiento = 0.45; resolución de 640 px."))
add(leyenda("Figura", nf, "Matriz de confusión del modelo de frutos en el conjunto de prueba"))
add(img.drawing(S / "fig/cm_frutos.png", 15.5, "Matriz de confusión del modelo de frutos"))
add(nota("Elaboración propia. Valores normalizados por fila (clase real) y, entre paréntesis, número de instancias. "
         "Umbral de confianza = 0.35; IoU de emparejamiento = 0.45."))
add(parrafo(
    f"En el modelo de hojas del servidor (Figura {nh}), la deficiencia nutricional se reconoció en el 97.1 % de los casos, "
    "la hoja sana en el 85.5 % y la antracnosis en el 79.7 %. La clase de plagas concentró los errores: el 19.1 % de los "
    "daños por trips y ácaros no fue detectado y el 8.8 % se confundió con antracnosis, debido a que ambas afecciones "
    "producen manchas necróticas en la lámina foliar. La confusión más relevante desde el punto de vista fitosanitario fue "
    "la de hojas con antracnosis clasificadas como sanas (14.5 %), que corresponde a lesiones incipientes de poco "
    f"contraste. El modelo de tiempo real (Figura {nr}) redujo esta confusión al 7.2 % y elevó el reconocimiento de la "
    "antracnosis al 84.1 % y de las plagas al 70.6 %, aunque omitió un mayor número de hojas sanas (13.0 %), error que no "
    "afecta el diagnóstico fitosanitario porque no genera alertas. "
    f"En el modelo de frutos (Figura {nf}), las confusiones entre enfermedades fueron poco frecuentes —la más relevante fue "
    "la de roña clasificada como antracnosis (15.1 %)—, mientras que el error predominante fue la omisión: el 36.5 % de las "
    "lesiones de antracnosis y el 24.5 % de las de roña no fueron localizadas. Este patrón indicó que, cuando el modelo "
    "emitió una detección, la clase asignada fue mayoritariamente correcta, y que su principal limitación residió en la "
    "sensibilidad frente a lesiones poco visibles, aspecto que se analiza en la sección de detección temprana."))
n = next(F)
add(leyenda("Figura", n, "Sensibilidad (recall) por clase en el conjunto de prueba"))
add(img.drawing(S / "fig/recall.png", 15.5, "Sensibilidad por clase"))
add(nota("Elaboración propia. Las barras grises corresponden a las clases sanas y la línea punteada al umbral del 70 %."))

add(parrafo(
    "Dado que en la práctica de campo la decisión relevante para el productor es si una hoja o un fruto presenta o no una "
    "afección, se evaluó también la precisión diagnóstica a nivel de imagen. Para ello, una imagen se consideró afectada si "
    "contenía al menos una etiqueta de enfermedad o plaga, y el sistema la clasificó como alerta si emitió al menos una "
    "detección de enfermedad con confianza igual o superior a 0.35, que es el mismo criterio que aplica la aplicación "
    "desplegada. Los resultados se presentan en la Tabla 8."))
t = next(T)
add(leyenda("Tabla", t, "Precisión diagnóstica a nivel de imagen (afectada frente a sana)"))
ci = lambda d, k: f"{pct(d[k][0])} ({ic(d[k])})"
add(tabla(["Indicador", "Hojas (servidor)", "Hojas (tiempo real)", "Frutos (servidor)"], [
    ["Imágenes evaluadas", str(hi["n"]), str(ri["n"]), str(fi["n"])],
    ["Verdaderos positivos / falsos negativos", f"{hi['TP']} / {hi['FN']}", f"{ri['TP']} / {ri['FN']}", f"{fi['TP']} / {fi['FN']}"],
    ["Verdaderos negativos / falsos positivos", f"{hi['TN']} / {hi['FP']}", f"{ri['TN']} / {ri['FP']}", f"{fi['TN']} / {fi['FP']}"],
    ["Sensibilidad", ci(hi, "sensibilidad"), ci(ri, "sensibilidad"), ci(fi, "sensibilidad")],
    ["Especificidad", ci(hi, "especificidad"), ci(ri, "especificidad"), ci(fi, "especificidad")],
    ["Valor predictivo positivo", ci(hi, "vpp"), ci(ri, "vpp"), ci(fi, "vpp")],
    ["Exactitud (accuracy)", ci(hi, "exactitud"), ci(ri, "exactitud"), ci(fi, "exactitud")],
    ["Kappa de Cohen (κ)", f"{hi['kappa']:.3f}", f"{ri['kappa']:.3f}", f"{fi['kappa']:.3f}"],
], [2500, 2250, 2250, 2250]))
add(nota("Elaboración propia. Entre paréntesis, intervalo de confianza al 95 % calculado con el método de Wilson. "
         "Umbral de confianza = 0.35."))
add(parrafo(
    f"Los resultados de la Tabla 8 evidenciaron que el sistema identificó correctamente el {pct(hi['sensibilidad'][0])} de "
    f"las hojas afectadas con el modelo del servidor, el {pct(ri['sensibilidad'][0])} con el modelo de tiempo real y el "
    f"{pct(fi['sensibilidad'][0])} de los frutos afectados, con una especificidad de {pct(hi['especificidad'][0])}, "
    f"{pct(ri['especificidad'][0])} y {pct(fi['especificidad'][0])}, respectivamente. La exactitud diagnóstica fue de "
    f"{pct(hi['exactitud'][0])} y {pct(ri['exactitud'][0])} para hojas y de {pct(fi['exactitud'][0])} para frutos. "
    "Asimismo, el valor predictivo positivo superó el 96 % en los tres modelos, lo que significó que casi la totalidad de "
    "las alertas emitidas correspondieron a una afección real. El coeficiente kappa de Cohen indicó un acuerdo sustancial "
    f"para ambos modelos de hojas (κ = {hi['kappa']:.3f} y κ = {ri['kappa']:.3f}) y moderado para el modelo de frutos "
    f"(κ = {fi['kappa']:.3f}) entre el diagnóstico del sistema y el etiquetado de referencia, según la escala de Landis y "
    "Koch (1977)."))

add(subtitulo("Verificación con imágenes procesadas en el sistema desplegado"))
add(parrafo(
    "De manera complementaria, se revisaron las 18 inspecciones registradas en el historial de la aplicación desplegada y "
    "exportadas en el reporte PDF del 19 de octubre de 2026. Se excluyeron seis registros (33.3 %) en los que el órgano "
    "seleccionado no correspondió a la imagen capturada: cinco imágenes de frutos registradas como hoja (inspecciones 10, "
    "12, 13, 14 y 16) y una imagen de hoja registrada como fruto (inspección 7). Las 12 inspecciones válidas se presentan "
    "en la Tabla 9."))
t = next(T)
add(leyenda("Tabla", t, "Inspecciones válidas registradas en el sistema desplegado"))
insp = [
    ("1", "Fruto", "Antracnosis en fruto (54.4 %)", "Alerta"),
    ("2", "Fruto", "Antracnosis en fruto (82.7 %); roña (51.8 %)", "Alerta"),
    ("3", "Fruto", "Antracnosis en fruto (36.3 %)", "Alerta"),
    ("4", "Fruto", "Cercospora (90.1 %)", "Alerta"),
    ("5", "Fruto", "Antracnosis en fruto (62.6 %)", "Alerta"),
    ("6", "Fruto", "Antracnosis en fruto (74.6 % y 60.3 %)", "Alerta"),
    ("8", "Fruto", "Pudrición peduncular (96.9 %)", "Alerta"),
    ("9", "Fruto", "Antracnosis en fruto (81.3 %)", "Alerta"),
    ("11", "Fruto", "Antracnosis en fruto (93.6 %); roña (80.1 %)", "Alerta"),
    ("15", "Hoja", "Hoja sana (71.2 %)", "Sano"),
    ("17", "Hoja", "Plagas: trips/ácaros (60.6 %)", "Alerta"),
    ("18", "Hoja", "Hoja sana (93.7 % y 79.5 %)", "Sano"),
]
add(tabla(["N.°", "Órgano", "Detecciones (confianza)", "Veredicto"], [list(r) for r in insp],
          [700, 1100, 4800, 1300], ["center", "left", "left", "center"]))
add(nota("Elaboración propia a partir del reporte de inspección fitosanitaria exportado por el sistema. Las inspecciones se "
         "registraron el 7 de octubre de 2026, antes de la actualización de los modelos de frutos (19 de octubre de 2026) y "
         "de hojas (20 de octubre de 2026), por lo que corresponden a las versiones anteriores de ambos modelos."))
confs = [54.4, 82.7, 51.8, 36.3, 90.1, 62.6, 74.6, 60.3, 96.9, 81.3, 93.6, 80.1, 71.2, 60.6, 93.7, 79.5]
add(parrafo(
    f"En las 12 inspecciones válidas el sistema emitió {len(confs)} detecciones, con una confianza media de "
    f"{sum(confs) / len(confs):.1f} % (mínimo 36.3 % y máximo 96.9 %). Nueve frutos generaron una alerta fitosanitaria, "
    "con predominio de la antracnosis (siete casos), y de las tres hojas evaluadas dos se clasificaron como sanas y una con "
    "daño por plagas. La proporción de registros con el órgano mal seleccionado evidenció que el paso de selección manual "
    "del órgano constituyó la principal fuente de error operativo del sistema. "
    "[[La concordancia de estos diagnósticos con el criterio del especialista agrónomo queda pendiente de registro.]]"))

# ---------------------------------------------------------------- OE2
add(subtitulo("Resultados del objetivo específico 2: tiempo de inspección"))
tf, th, tr = FR["tiempo_ms"], HO["tiempo_ms"], RT["tiempo_ms"]
add(parrafo(
    "El tiempo de procesamiento constituyó el componente del tiempo de inspección atribuible directamente al sistema. Se "
    "midió el tiempo total de inferencia por imagen (lectura, preprocesamiento, inferencia y posprocesamiento) sobre el "
    "conjunto de prueba, excluyendo las tres primeras imágenes de calentamiento. Los resultados se muestran en la Tabla 10."))
t = next(T)
add(leyenda("Tabla", t, "Tiempo de procesamiento por imagen del sistema"))
add(tabla(["Modelo", "n", "Media (ms)", "DE (ms)", "Mediana (ms)", "Percentil 95 (ms)", "Imágenes por minuto"], [
    ["Hojas (servidor)", str(th["n"]), f"{th['media']:.1f}", f"{th['de']:.1f}", f"{th['mediana']:.1f}", f"{th['p95']:.1f}", f"{60000 / th['media']:.0f}"],
    ["Hojas (tiempo real)", str(tr["n"]), f"{tr['media']:.1f}", f"{tr['de']:.1f}", f"{tr['mediana']:.1f}", f"{tr['p95']:.1f}", f"{60000 / tr['media']:.0f}"],
    ["Frutos (servidor)", str(tf["n"]), f"{tf['media']:.1f}", f"{tf['de']:.1f}", f"{tf['mediana']:.1f}", f"{tf['p95']:.1f}", f"{60000 / tf['media']:.0f}"],
], [1900, 600, 1050, 900, 1150, 1350, 1350]))
add(nota("Elaboración propia. Medición en CPU Intel Core i7-12700 (sin GPU), a 1024 px para los modelos del servidor y a "
         "640 px para el modelo de tiempo real. DE = desviación estándar."))
add(parrafo(
    f"Como se observa en la Tabla 10, los modelos del servidor procesaron una imagen de hoja en {th['media']:.1f} ms en "
    f"promedio y una imagen de fruto en {tf['media']:.1f} ms, lo que equivale a más de 100 imágenes por minuto en el caso "
    "más lento. Aunque estos valores superaron la meta referencial de 150 ms por imagen, el tiempo de respuesta se mantuvo "
    "por debajo de un segundo, por lo que el diagnóstico se obtuvo prácticamente de forma inmediata tras la captura. El "
    f"modelo ligero de hojas redujo el tiempo de procesamiento a {tr['media']:.1f} ms (mediana de {tr['mediana']:.1f} ms), "
    f"es decir, {th['media'] / tr['media']:.1f} veces menos que el modelo del servidor, y cumplió la meta de 150 ms incluso "
    f"en el percentil 95 ({tr['p95']:.1f} ms), sin pérdida de precisión diagnóstica (Tabla 6). Este resultado respaldó su "
    "uso en el modo de inspección en tiempo real, en el que el recorrido por el campo se apoya en un diagnóstico continuo "
    "sobre la imagen de la cámara. La comparación del tiempo de inspección por árbol entre la inspección manual "
    "(preprueba) y la "
    "inspección asistida por el sistema (posprueba) se presenta en la Tabla 11."))
t = next(T)
add(leyenda("Tabla", t, "Tiempo de inspección por árbol antes y después de la implementación"))
P = "[[Pendiente]]"
add(tabla(["Indicador", "Preprueba (manual)", "Posprueba (con sistema)", "Diferencia", "Reducción (%)"], [
    ["Tiempo promedio por árbol (min)", P, P, P, P],
    ["Tiempo total por hectárea (min)", P, P, P, P],
], [2800, 1500, 1700, 1300, 1300]))
add(nota("Elaboración propia. Datos de las fichas de observación de los 100 árboles muestreados (50 del sector A y 50 del "
         "sector B). [[Completar con los tiempos cronometrados en campo.]]"))

# ---------------------------------------------------------------- OE3
add(subtitulo("Resultados del objetivo específico 3: disminución de las pérdidas por descarte"))
add(parrafo(
    "La disminución de las pérdidas por descarte se abordó a partir de la capacidad del sistema para detectar las "
    "enfermedades de manera oportuna, puesto que un fruto o una hoja afectados que se identifican a tiempo permiten aplicar "
    "medidas de control antes de que la afección comprometa la calidad comercial del fruto. Para ello, se calculó la tasa "
    "de detección por enfermedad, entendida como el porcentaje de imágenes con una afección determinada en las que el sistema "
    "detectó esa misma afección. Los resultados se presentan en la Tabla 12."))
t = next(T)
add(leyenda("Tabla", t, "Tasa de detección por enfermedad en el conjunto de prueba"))
filas = []
for nom, d in (("Hoja (servidor)", HO), ("Hoja (tiempo real)", RT), ("Fruto (servidor)", FR)):
    for k, v in d["deteccion_por_enfermedad"].items():
        filas.append([nom, ETQ[k], str(v["presentes"]), str(v["detectadas"]), pct(v["tasa"][0]), ic(v["tasa"])])
add(tabla(["Modelo", "Enfermedad o plaga", "Imágenes con la afección", "Detectadas", "Tasa de detección", "IC 95 %"],
          filas, [1650, 2250, 1350, 1100, 1200, 1350], ["left", "left"] + ["center"] * 4))
add(nota("Elaboración propia. Una afección se consideró detectada si el sistema emitió al menos una detección de esa clase "
         "con confianza ≥ 0.35. Intervalos de Wilson."))
de_f, de_h, de_r = FR["deteccion_por_enfermedad"], HO["deteccion_por_enfermedad"], RT["deteccion_por_enfermedad"]
add(parrafo(
    "Los resultados de la Tabla 12 mostraron que todas las afecciones superaron una tasa de detección del 70 %. En los "
    f"frutos, la cercospora alcanzó la mayor tasa ({pct(de_f['cercospora']['tasa'][0])}), seguida de la roña "
    f"({pct(de_f['rona']['tasa'][0])}), la pudrición peduncular ({pct(de_f['pudricion_peduncular']['tasa'][0])}), "
    f"el sunblotch ({pct(de_f['sunblotch']['tasa'][0])}) y la antracnosis ({pct(de_f['antracnosis_fruto']['tasa'][0])}). "
    f"En las hojas, con el modelo del servidor, la deficiencia nutricional fue detectada en el "
    f"{pct(de_h['deficiencia_nutricional']['tasa'][0])} de los casos, la antracnosis en el "
    f"{pct(de_h['antracnosis_hoja']['tasa'][0])} y las plagas en el {pct(de_h['plaga']['tasa'][0])}; el modelo de tiempo "
    f"real obtuvo tasas equivalentes ({pct(de_r['deficiencia_nutricional']['tasa'][0])}, "
    f"{pct(de_r['antracnosis_hoja']['tasa'][0])} y {pct(de_r['plaga']['tasa'][0])}, respectivamente). La detección de la "
    "antracnosis en la hoja resultó especialmente relevante, debido a que el follaje infectado constituye la principal "
    "fuente de inóculo del hongo hacia el fruto y a que la antracnosis es la principal causa de descarte del fruto en "
    "poscosecha; por ello, su identificación en hoja permitió anticipar medidas de control antes de que la enfermedad "
    "alcanzara el fruto."))
add(parrafo(
    "Con el fin de aproximar la capacidad de detección temprana, se analizó la sensibilidad del sistema según el tamaño de "
    "la lesión, considerando que las lesiones de menor tamaño corresponden, por lo general, a estadios iniciales de la "
    "enfermedad. Se calculó el porcentaje de lesiones etiquetadas que fueron localizadas por el sistema con la clase correcta "
    "(IoU ≥ 0.50), agrupadas según la proporción del área de la imagen que ocupaban (Tabla 13)."))
t = next(T)
add(leyenda("Tabla", t, "Sensibilidad según el tamaño de la lesión"))
st_f, st_h, st_r = FR["sensibilidad_por_tamano"], HO["sensibilidad_por_tamano"], RT["sensibilidad_por_tamano"]
fila = lambda d, k: (f"{d[k]['detectadas']} / {d[k]['total']} ({pct(d[k]['tasa'][0])})" if d[k]["total"] else "0 / 0 (—)")
filas = []
for k, et in (("pequena (<2%)", "Pequeña (< 2 %)"), ("mediana (2-10%)", "Mediana (2 % – 10 %)"), ("grande (>10%)", "Grande (> 10 %)")):
    filas.append([et, fila(st_h, k), fila(st_r, k), fila(st_f, k)])
add(tabla(["Tamaño de la lesión", "Hojas (servidor)", "Hojas (tiempo real)", "Frutos (servidor)"],
          filas, [2500, 2150, 2150, 2150]))
add(nota("Elaboración propia. Tamaño expresado como proporción del área de la imagen ocupada por la caja delimitadora de "
         "la lesión. Se excluyeron las clases sanas. Cada celda indica lesiones detectadas / lesiones etiquetadas (porcentaje)."))
add(parrafo(
    f"Como se aprecia en la Tabla 13, la sensibilidad del sistema dependió del tamaño de la lesión: en los frutos, se "
    f"localizó el {pct(st_f['grande (>10%)']['tasa'][0])} de las lesiones grandes, el "
    f"{pct(st_f['mediana (2-10%)']['tasa'][0])} de las medianas y ninguna de las 17 lesiones pequeñas; en las hojas, el "
    f"modelo del servidor localizó el {pct(st_h['grande (>10%)']['tasa'][0])} de las lesiones grandes y el "
    f"{pct(st_h['mediana (2-10%)']['tasa'][0])} de las medianas, mientras que el modelo de tiempo real alcanzó el "
    f"{pct(st_r['grande (>10%)']['tasa'][0])} y el {pct(st_r['mediana (2-10%)']['tasa'][0])}, respectivamente. El conjunto "
    "de prueba de hojas no contuvo lesiones pequeñas y solo 14 medianas, por lo que estos porcentajes deben interpretarse "
    "con cautela. Este resultado indicó que la detección temprana fue "
    "efectiva cuando la lesión ocupó una porción visible del órgano fotografiado, por lo que el protocolo de captura en "
    "campo debió privilegiar tomas cercanas que encuadren un solo fruto u hoja. La comparación del descarte antes y "
    "después de la implementación se presenta en la Tabla 14."))
t = next(T)
add(leyenda("Tabla", t, "Pérdidas por descarte antes y después de la implementación"))
add(tabla(["Indicador", "Preprueba", "Posprueba", "Diferencia", "Reducción (%)"], [
    ["Frutos descartados (%)", P, P, P, P],
    ["Frutos exportables (%)", P, P, P, P],
    ["Pérdidas económicas estimadas (S/)", P, P, P, P],
], [3000, 1400, 1400, 1300, 1400]))
add(nota("Elaboración propia. [[Completar con los conteos de frutos descartados y exportables registrados en campo y el "
         "cuestionario de evaluación agronómica.]]"))

# ---------------------------------------------------------------- hipotesis
add(subtitulo("Contraste de hipótesis"))
add(parrafo(
    "Para la hipótesis específica 1 se contrastó si la exactitud diagnóstica del sistema superaba el umbral mínimo de "
    "desempeño del 70 % (H0: p ≤ 0.70; H1: p > 0.70) mediante la prueba binomial exacta unilateral, con un nivel de "
    "significancia de 0.05. Adicionalmente, se contrastó la exactitud frente a la meta de coincidencia del 85 % establecida "
    "en la matriz de operacionalización. Los resultados se presentan en la Tabla 15."))
t = next(T)
add(leyenda("Tabla", t, "Prueba binomial exacta de la exactitud diagnóstica"))
def _fila(nom, d):
    k, n = d["TP"] + d["TN"], d["n"]
    p70, p85 = binom_p(k, n, 0.70), binom_p(k, n, 0.85)
    dec = ("Se rechaza H0 en ambos umbrales" if p85 < 0.05 else "Se rechaza H0 solo para el 70 %") if p70 < 0.05 \
        else "No se rechaza H0"
    return [nom, f"{k} / {n}", pct(d["exactitud"][0]), fp(p70), fp(p85), dec], p70, p85
f_h, ph70, ph85 = _fila("Hojas (servidor)", hi)
f_r, pr70, pr85 = _fila("Hojas (tiempo real)", ri)
f_f, pf70, pf85 = _fila("Frutos (servidor)", fi)
print("binomial", f_h, f_r, f_f)
add(tabla(["Modelo", "Aciertos / n", "Exactitud", "p (H0: p ≤ 0.70)", "p (H0: p ≤ 0.85)", "Decisión"],
          [f_h, f_r, f_f], [1700, 1150, 1050, 1350, 1350, 2400]))
add(nota("Elaboración propia. Prueba binomial exacta unilateral (α = 0.05) sobre el split de prueba."))
add(parrafo(
    "Los resultados permitieron rechazar la hipótesis nula para el umbral del 70 % en los tres modelos (p < 0.001), con lo "
    "cual se aceptó la hipótesis específica 1: la implementación del sistema de visión computacional mejoró "
    "significativamente la precisión en el diagnóstico fitosanitario de la palta Hass, con un desempeño igual o superior "
    f"al 70 % en mAP50 (hojas: {pct(hj['mAP50'])} en el servidor y {pct(rg['mAP50'])} en tiempo real; frutos: "
    f"{pct(fg['mAP50'])}). Respecto de la meta del 85 %, ambos modelos de hojas la superaron de forma significativa "
    f"(p {'< 0.001' if ph85 < 0.001 else '= ' + fp(ph85)} y p {'< 0.001' if pr85 < 0.001 else '= ' + fp(pr85)}), mientras "
    f"que en el modelo de frutos la diferencia no fue significativa (p = {fp(pf85)})."))
add(parrafo(
    "Las hipótesis específicas 2 y 3, así como la hipótesis general, requieren las mediciones de preprueba y posprueba "
    "realizadas en los 100 árboles de la muestra. Para su contraste se aplicará la prueba de normalidad de Shapiro-Wilk a "
    "las diferencias pareadas y, según su resultado, la prueba t de Student para muestras relacionadas o la prueba de "
    "rangos con signo de Wilcoxon. [[Pendiente: completar con los datos de campo.]]"))

# ---------------------------------------------------------------- insercion
xml = DOC.read_text(encoding="utf8")
_cap3 = [m.start() for m in re.finditer("CAPÍTULO III", xml)][-1]
_pre, _post = xml[:_cap3], xml[_cap3:]
_k = [0]
def _renum(m):
    _k[0] += 1
    return m.group(1) + str(_k[0]) + m.group(3)
_pre = re.sub(r'(SEQ Tabla \\\* ARABIC </w:instrText>.*?<w:t>)(\d+)(</w:t>)', _renum, _pre, flags=re.S)
xml = _pre + _post
print("tablas Cap. II renumeradas:", _k[0])
a = [m.start() for m in re.finditer("CAPÍTULO III", xml)][-1]
ini = xml.find("</w:p>", a) + 6                        # fin del parrafo del titulo
b = [m.start() for m in re.finditer("CAPÍTULO IV", xml)][-1]
fin = xml.rfind("<w:p ", 0, b)                         # inicio del parrafo del titulo del Cap. IV
viejo = xml[ini:fin]
# conservar el ultimo salto de seccion del capitulo
ult = viejo.rfind("<w:sectPr")
ps = max(viejo.rfind("<w:p ", 0, ult), viejo.rfind("<w:p>", 0, ult))
pe = viejo.find("</w:p>", ult) + 6
psect = viejo[ps:pe]
psect = re.sub(r"<w:r[ >].*?</w:r>", "", psect[:psect.find("</w:pPr>") + 8], flags=re.S) + "</w:p>"
xml = xml[:ini] + "".join(x) + psect + xml[fin:]
DOC.write_text(xml, encoding="utf8")
print("tablas hasta", t, "figuras hasta", n, "imagenes", img.n)
