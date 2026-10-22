"""Reemplaza la plantilla del Cap. III (tesis de referencia) por los resultados de la tesis de palta Hass."""
import json, re, sys
from pathlib import Path

S = Path(__file__).parent
sys.path.insert(0, str(S))
from docxlib import parrafo, subtitulo, nota, leyenda, tabla, Imagenes

U = S / "work/v6"
SIM = json.loads((S / "sim_resultados.json").read_text(encoding="utf8"))
DOC = U / "word/document.xml"
FR = json.loads((S / "eval_frutos.json").read_text(encoding="utf8"))
HO = json.loads((S / "eval_hojas_rt.json").read_text(encoding="utf8"))   # hojas.pt = hojas_tiempo_real (YOLO11n, 640 px)


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
fg, hj = FR["global"], HO["global"]
fi, hi = FR["imagen"], HO["imagen"]

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
    "(hoja o fruto) y el sistema la procesó con el modelo YOLO11 correspondiente. Las detecciones con una confianza igual o "
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
     "Medición en el split de prueba; simulación de resultados esperados (100 árboles)"],
    ["OE3. Pérdidas por descarte", "Pérdidas por descarte (detección temprana)",
     "Tasa de detección por enfermedad; sensibilidad según tamaño de lesión; % de frutos descartados",
     "Split de prueba del dataset; simulación de resultados esperados (100 árboles)"],
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
    "Ambos modelos se entrenaron a partir de arquitecturas YOLO11 preentrenadas. El modelo de hojas empleó la variante "
    "ligera YOLO11n con una resolución de entrada de 640 píxeles, lo que permitió obtener el diagnóstico en tiempo real "
    "durante el recorrido por el campo; el modelo de frutos empleó la variante YOLO11s con una resolución de 1024 píxeles, "
    "debido a que las lesiones del fruto son de menor tamaño y contraste. La configuración empleada se detalla en la "
    "Tabla 5."))
t = next(T)
add(leyenda("Tabla", t, "Configuración del entrenamiento de los modelos"))
add(tabla(["Parámetro", "Modelo de hojas", "Modelo de frutos"], [
    ["Arquitectura base", "YOLO11n (preentrenado)", "YOLO11s (preentrenado)"],
    ["Resolución de entrada", "640 px", "1024 px"],
    ["Épocas programadas / ejecutadas", "180 / 179", "200 / 109"],
    ["Paciencia (parada temprana)", "40 épocas", "40 épocas"],
    ["Tamaño de lote", "32", "8"],
    ["Optimizador y tasa inicial", "Automático, 0.01", "Automático, 0.01"],
    ["Programación de la tasa de aprendizaje", "Coseno", "Coseno"],
    ["Mejor época (validación)", "139", "93"],
    ["mAP50 en validación (mejor época)", pct(0.90728), pct(0.78683)],
    ["mAP50-95 en validación (mejor época)", pct(0.84644), pct(0.59137)],
], [3400, 2600, 2600]))
add(nota("Elaboración propia a partir de los archivos args.yaml y results.csv generados por Ultralytics durante el entrenamiento."))
n = next(F)
add(parrafo(f"La Figura {n} muestra la evolución de las métricas mAP50 y mAP50-95 en el conjunto de validación durante el "
            "entrenamiento. En ambos modelos la curva de mAP50 superó el umbral del 70 % y se estabilizó en las últimas "
            "épocas, lo que indicó que el entrenamiento convergió sin evidencias de sobreajuste severo. El modelo de hojas "
            "superó el umbral antes de la décima época, se estabilizó por encima del 90 % de mAP50 y finalizó por parada "
            "temprana en la época 179, al no mejorar durante 40 épocas consecutivas desde la época 139. El modelo de frutos "
            "requirió alrededor de 25 épocas para superar el umbral y se estabilizó cerca del 78 %, lo que reflejó la mayor "
            "dificultad de esta tarea, con seis clases y lesiones de menor contraste sobre la cáscara oscura del fruto."))
add(leyenda("Figura", n, "Evolución de mAP50 y mAP50-95 durante el entrenamiento"))
add(img.drawing(S / "fig/curvas2.png", 15.5, "Curvas de entrenamiento"))
add(nota("Elaboración propia. La línea punteada representa el umbral mínimo de desempeño (mAP50 = 70 %) establecido en la "
         "hipótesis específica 1."))

# ---------------------------------------------------------------- OE1
add(subtitulo("Resultados del objetivo específico 1: precisión en el diagnóstico fitosanitario"))
add(parrafo(
    "Para determinar la precisión del diagnóstico, ambos modelos se evaluaron sobre el conjunto de prueba, conformado por "
    "imágenes que no participaron en el entrenamiento ni en la selección del modelo. Los resultados globales se presentan "
    "en la Tabla 6, junto con el nivel alcanzado según la escala definida en la matriz de operacionalización (alto si "
    "mAP50 ≥ 85 %, aceptable entre 70 % y 84 %, y bajo si es menor de 70 %)."))
t = next(T)
add(leyenda("Tabla", t, "Desempeño global de los modelos en el conjunto de prueba"))
add(tabla(["Modelo", "Precisión (P)", "Recall (R)", "F1-score", "mAP50", "mAP50-95", "Nivel"], [
    ["Hojas", pct(hj["P"]), pct(hj["R"]), pct(hj["F1"]), pct(hj["mAP50"]), pct(hj["mAP50_95"]), nivel(hj["mAP50"])],
    ["Frutos", pct(fg["P"]), pct(fg["R"]), pct(fg["F1"]), pct(fg["mAP50"]), pct(fg["mAP50_95"]), nivel(fg["mAP50"])],
], [1200, 1300, 1200, 1200, 1100, 1200, 1300]))
add(nota("Elaboración propia. Evaluación con Ultralytics sobre el split de prueba (237 imágenes de hojas y 381 de frutos), "
         "con umbral de IoU de 0.50 para mAP50. Resolución de evaluación: 640 px para hojas y 1024 px para frutos."))
add(parrafo(
    f"Como se aprecia en la Tabla 6, el modelo de hojas alcanzó un mAP50 de {pct(hj['mAP50'])} y un F1-score de "
    f"{pct(hj['F1'])}, mientras que el modelo de frutos obtuvo un mAP50 de {pct(fg['mAP50'])} y un F1-score de "
    f"{pct(fg['F1'])}. Ambos modelos superaron el umbral mínimo del 70 % planteado en la hipótesis específica 1: el modelo "
    f"de hojas se ubicó en el nivel alto y el de frutos en el nivel aceptable. El modelo de frutos presentó una precisión ({pct(fg['P'])}) superior a su sensibilidad ({pct(fg['R'])}), lo que indicó que sus "
    "detecciones fueron mayoritariamente correctas, aunque omitió una parte de las lesiones presentes. El desempeño por "
    "clase se detalla en la Tabla 7."))
t = next(T)
add(leyenda("Tabla", t, "Desempeño por clase en el conjunto de prueba"))
filas = []
for nom, d in (("Hojas", HO), ("Frutos", FR)):
    for k, v in d["por_clase"].items():
        filas.append([nom, ETQ[k], pct(v["P"]), pct(v["R"]), pct(v["F1"]), pct(v["mAP50"]), pct(v["mAP50_95"])])
add(tabla(["Modelo", "Clase", "P", "R", "F1", "mAP50", "mAP50-95"], filas,
          [1000, 2400, 1000, 1000, 1000, 1100, 1200], ["left", "left"] + ["center"] * 5))
add(nota("Elaboración propia. Resultados por clase del split de prueba."))
pf, ph = FR["por_clase"], HO["por_clase"]
add(parrafo(
    "En el modelo de hojas, la deficiencia nutricional obtuvo el mejor desempeño (mAP50 = "
    f"{pct(ph['deficiencia_nutricional']['mAP50'])}), seguida de la antracnosis ({pct(ph['antracnosis_hoja']['mAP50'])}) y "
    f"de la hoja sana ({pct(ph['hoja_sana']['mAP50'])}); la clase de plagas registró el valor más bajo "
    f"({pct(ph['plaga']['mAP50'])}) y la menor sensibilidad ({pct(ph['plaga']['R'])}), debido a que los daños por trips y ácaros son pequeños y se confunden con otras "
    "alteraciones de la lámina foliar. En el modelo de frutos, sunblotch "
    f"({pct(pf['sunblotch']['mAP50'])}), cercospora ({pct(pf['cercospora']['mAP50'])}) y pudrición peduncular "
    f"({pct(pf['pudricion_peduncular']['mAP50'])}) superaron el 80 %, mientras que la antracnosis "
    f"({pct(pf['antracnosis_fruto']['mAP50'])}) y el fruto sano ({pct(pf['fruto_sano']['mAP50'])}) presentaron los valores "
    "más bajos, lo cual se asoció a la similitud visual entre las lesiones iniciales de antracnosis, las manchas de roña y "
    "el oscurecimiento natural de la cáscara del fruto Hass maduro."))
CM = json.loads((S / "cm_test.json").read_text(encoding="utf8"))
nh, nf = next(F), next(F)
add(parrafo(
    f"Para identificar el tipo de error cometido por cada modelo se elaboraron las matrices de confusión de las Figuras {nh} "
    f"y {nf}, calculadas con el mismo umbral de confianza que aplica el sistema desplegado (0.35) y un IoU mínimo de 0.45 "
    "para emparejar cada detección con su etiqueta. Las filas representan la clase real y las columnas la clase predicha; "
    "la columna «No detectado» agrupa las lesiones u órganos que el sistema no localizó y la fila «Fondo» las detecciones "
    "emitidas sobre zonas sin etiqueta (falsos positivos)."))
add(leyenda("Figura", nh, "Matriz de confusión del modelo de hojas en el conjunto de prueba"))
add(img.drawing(S / "fig/cm_hojas_rt.png", 11.5, "Matriz de confusión del modelo de hojas"))
add(nota("Elaboración propia. Valores normalizados por fila (clase real) y, entre paréntesis, número de instancias. "
         "Umbral de confianza = 0.35; IoU de emparejamiento = 0.45; resolución de 640 px."))
add(leyenda("Figura", nf, "Matriz de confusión del modelo de frutos en el conjunto de prueba"))
add(img.drawing(S / "fig/cm_frutos.png", 15.5, "Matriz de confusión del modelo de frutos"))
add(nota("Elaboración propia. Valores normalizados por fila (clase real) y, entre paréntesis, número de instancias. "
         "Umbral de confianza = 0.35; IoU de emparejamiento = 0.45."))
add(parrafo(
    f"En el modelo de hojas (Figura {nh}), la deficiencia nutricional se reconoció en el 97.1 % de los casos, la "
    "antracnosis en el 84.1 % y la hoja sana en el 79.7 %. La clase de plagas concentró los errores: el 17.6 % de los daños "
    "por trips y ácaros no fue detectado y el 7.4 % se confundió con antracnosis, debido a que ambas afecciones producen "
    "manchas necróticas en la lámina foliar. Solo el 7.2 % de las hojas con antracnosis se clasificó como sana, mientras "
    "que el 13.0 % de las hojas sanas no fue localizado, error que no afecta el diagnóstico porque no genera alertas. "
    f"En el modelo de frutos (Figura {nf}), las confusiones entre enfermedades fueron poco frecuentes —la más relevante fue "
    "la de roña clasificada como antracnosis (15.1 %)—, mientras que el error predominante fue la omisión: el 36.5 % de las "
    "lesiones de antracnosis y el 24.5 % de las de roña no fueron localizadas. Este patrón indicó que, cuando el modelo "
    "emitió una detección, la clase asignada fue mayoritariamente correcta, y que su principal limitación residió en la "
    "sensibilidad frente a lesiones poco visibles, aspecto que se analiza en la sección de detección temprana."))
n = next(F)
add(leyenda("Figura", n, "Sensibilidad (recall) por clase en el conjunto de prueba"))
add(img.drawing(S / "fig/recall2.png", 15.5, "Sensibilidad por clase"))
add(nota("Elaboración propia. Las barras grises corresponden a las clases sanas y la línea punteada al umbral del 70 %."))

add(parrafo(
    "Dado que en la práctica de campo la decisión relevante para el productor es si una hoja o un fruto presenta o no una "
    "afección, se evaluó también la precisión diagnóstica a nivel de imagen. Para ello, una imagen se consideró afectada si "
    "contenía al menos una etiqueta de enfermedad o plaga, y el sistema la clasificó como alerta si emitió al menos una "
    "detección de enfermedad con confianza igual o superior a 0.35, que es el mismo criterio que aplica la aplicación "
    "desplegada. Los resultados se presentan en la Tabla 8."))
t = next(T)
add(leyenda("Tabla", t, "Precisión diagnóstica a nivel de imagen (afectada frente a sana)"))
add(tabla(["Indicador", "Modelo de hojas", "IC 95 %", "Modelo de frutos", "IC 95 %"], [
    ["Imágenes evaluadas", str(hi["n"]), "", str(fi["n"]), ""],
    ["Verdaderos positivos / falsos negativos", f"{hi['TP']} / {hi['FN']}", "", f"{fi['TP']} / {fi['FN']}", ""],
    ["Verdaderos negativos / falsos positivos", f"{hi['TN']} / {hi['FP']}", "", f"{fi['TN']} / {fi['FP']}", ""],
    ["Sensibilidad", pct(hi["sensibilidad"][0]), ic(hi["sensibilidad"]), pct(fi["sensibilidad"][0]), ic(fi["sensibilidad"])],
    ["Especificidad", pct(hi["especificidad"][0]), ic(hi["especificidad"]), pct(fi["especificidad"][0]), ic(fi["especificidad"])],
    ["Valor predictivo positivo", pct(hi["vpp"][0]), ic(hi["vpp"]), pct(fi["vpp"][0]), ic(fi["vpp"])],
    ["Exactitud (accuracy)", pct(hi["exactitud"][0]), ic(hi["exactitud"]), pct(fi["exactitud"][0]), ic(fi["exactitud"])],
    ["Kappa de Cohen (κ)", f"{hi['kappa']:.3f}", "", f"{fi['kappa']:.3f}", ""],
], [3000, 1300, 1400, 1300, 1400]))
add(nota("Elaboración propia. Intervalos de confianza calculados con el método de Wilson. Umbral de confianza = 0.35."))
add(parrafo(
    f"Los resultados de la Tabla 8 evidenciaron que el sistema identificó correctamente el {pct(hi['sensibilidad'][0])} de "
    f"las hojas afectadas y el {pct(fi['sensibilidad'][0])} de los frutos afectados, con una especificidad de "
    f"{pct(hi['especificidad'][0])} y {pct(fi['especificidad'][0])}, respectivamente. La exactitud diagnóstica fue de "
    f"{pct(hi['exactitud'][0])} para hojas y {pct(fi['exactitud'][0])} para frutos. Asimismo, el valor predictivo positivo "
    f"superó el 96 % en ambos casos, lo que significó que casi la totalidad de las alertas emitidas correspondieron a una "
    f"afección real. El coeficiente kappa de Cohen indicó un acuerdo sustancial para hojas (κ = {hi['kappa']:.3f}) y "
    f"moderado para frutos (κ = {fi['kappa']:.3f}) entre el diagnóstico del sistema y el etiquetado de referencia, según "
    "la escala de Landis y Koch (1977)."))

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
tf, th = FR["tiempo_ms"], HO["tiempo_ms"]
add(parrafo(
    "El tiempo de procesamiento constituyó el componente del tiempo de inspección atribuible directamente al sistema. Se "
    "midió el tiempo total de inferencia por imagen (lectura, preprocesamiento, inferencia y posprocesamiento) sobre el "
    "conjunto de prueba, excluyendo las tres primeras imágenes de calentamiento. Los resultados se muestran en la Tabla 10."))
t = next(T)
add(leyenda("Tabla", t, "Tiempo de procesamiento por imagen del sistema"))
add(tabla(["Modelo", "n", "Media (ms)", "DE (ms)", "Mediana (ms)", "Percentil 95 (ms)", "Imágenes por minuto"], [
    ["Hojas", str(th["n"]), f"{th['media']:.1f}", f"{th['de']:.1f}", f"{th['mediana']:.1f}", f"{th['p95']:.1f}", f"{60000 / th['media']:.0f}"],
    ["Frutos", str(tf["n"]), f"{tf['media']:.1f}", f"{tf['de']:.1f}", f"{tf['mediana']:.1f}", f"{tf['p95']:.1f}", f"{60000 / tf['media']:.0f}"],
], [1100, 700, 1200, 1000, 1300, 1500, 1500]))
add(nota("Elaboración propia. Medición en CPU Intel Core i7-12700 (sin GPU), a 640 px para hojas y 1024 px para frutos. "
         "DE = desviación estándar."))
add(parrafo(
    f"Como se observa en la Tabla 10, el sistema procesó una imagen de hoja en {th['media']:.1f} ms en promedio (mediana de "
    f"{th['mediana']:.1f} ms), con lo que cumplió la meta de 150 ms por imagen incluso en el percentil 95 "
    f"({th['p95']:.1f} ms) y permitió el diagnóstico continuo sobre la imagen de la cámara. La imagen de fruto se procesó "
    f"en {tf['media']:.1f} ms, valor que superó la meta referencial de 150 ms debido a la mayor resolución del modelo; no "
    "obstante, el tiempo de respuesta se mantuvo por debajo de un segundo (más de 100 imágenes por minuto), por lo que el "
    "diagnóstico se obtuvo prácticamente de forma inmediata tras la captura. La comparación del tiempo de inspección por árbol entre la inspección manual (preprueba) y la "
    "inspección asistida por el sistema (posprueba) se presenta en la Tabla 11."))
t = next(T)
add(leyenda("Tabla", t, "Tiempo de inspección antes y después de la implementación (resultados esperados por simulación)"))
P = "[[Pendiente]]"
ms = lambda d, k: f"{d['media_' + k]:.1f} ± {d['de_' + k]:.1f}"
ta, tr_, tot = SIM["tiempo_arbol"], SIM["tiempo_respuesta"], SIM["totales"]
add(tabla(["Indicador", "Preprueba (manual)", "Posprueba (con sistema)", "Diferencia", "Reducción (%)"], [
    ["Tiempo de inspección por árbol (min)", ms(ta, "pre"), ms(ta, "post"), f"{ta['dif']:.1f}", f"{ta['reduccion'] * 100:.1f}"],
    ["Tiempo desde la detección del síntoma hasta el diagnóstico (h)", ms(tr_, "pre"), ms(tr_, "post"),
     f"{tr_['dif']:.1f}", f"{tr_['reduccion'] * 100:.1f}"],
    ["Tiempo estimado de inspección por hectárea (h)", f"{tot['ha_pre_h']:.1f}", f"{tot['ha_post_h']:.1f}",
     f"{tot['ha_pre_h'] - tot['ha_post_h']:.1f}", f"{(1 - tot['ha_post_h'] / tot['ha_pre_h']) * 100:.1f}"],
], [3100, 1500, 1600, 1100, 1200]))
add(nota("Elaboración propia. **Datos simulados** para los 100 árboles de la muestra (50 del sector A y 50 del sector B), "
         "expresados como media ± desviación estándar. Supuestos: inspección visual manual de hojas y frutos frente a la "
         "captura de cuatro hojas y cuatro frutos con el sistema; en la preprueba, espera de la visita del técnico y, en la "
         "posprueba, diagnóstico inmediato con confirmación remota del técnico; densidad de 625 árboles por hectárea. "
         "Estos valores serán reemplazados por las mediciones de las fichas de observación en la tesis."))
add(parrafo(
    "Los resultados esperados de la Tabla 11, obtenidos mediante simulación, indicaron que el tiempo de inspección por "
    f"árbol se reduciría de {ta['media_pre']:.1f} a {ta['media_post']:.1f} minutos en promedio, es decir, un "
    f"{ta['reduccion'] * 100:.1f} % menos, debido a que el sistema reemplaza la revisión visual detallada de cada órgano por "
    "la captura de imágenes y la lectura inmediata del diagnóstico. La mayor diferencia se presentaría en el tiempo "
    f"transcurrido desde que se observa un síntoma hasta contar con un diagnóstico: en la práctica habitual, el productor "
    f"debe esperar la visita del técnico ({tr_['media_pre']:.1f} horas en promedio), mientras que con el sistema el "
    "diagnóstico se obtiene al momento de la captura y la imagen puede enviarse al técnico para su confirmación remota "
    f"({tr_['media_post']:.1f} horas en promedio), lo que representaría una reducción del {tr_['reduccion'] * 100:.1f} %. "
    "Esta ventana de tiempo resulta determinante para la detección temprana, ya que permite iniciar las medidas de control "
    "antes de que la enfermedad avance."))

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
for nom, d in (("Hoja", HO), ("Fruto", FR)):
    for k, v in d["deteccion_por_enfermedad"].items():
        filas.append([nom, ETQ[k], str(v["presentes"]), str(v["detectadas"]), pct(v["tasa"][0]), ic(v["tasa"])])
add(tabla(["Órgano", "Enfermedad o plaga", "Imágenes con la afección", "Detectadas", "Tasa de detección", "IC 95 %"],
          filas, [1000, 2400, 1500, 1200, 1300, 1400], ["left", "left"] + ["center"] * 4))
add(nota("Elaboración propia. Una afección se consideró detectada si el sistema emitió al menos una detección de esa clase "
         "con confianza ≥ 0.35. Intervalos de Wilson."))
de_f, de_h = FR["deteccion_por_enfermedad"], HO["deteccion_por_enfermedad"]
add(parrafo(
    "Los resultados de la Tabla 12 mostraron que todas las afecciones superaron una tasa de detección del 70 %. En los "
    f"frutos, la cercospora alcanzó la mayor tasa ({pct(de_f['cercospora']['tasa'][0])}), seguida de la roña "
    f"({pct(de_f['rona']['tasa'][0])}), la pudrición peduncular ({pct(de_f['pudricion_peduncular']['tasa'][0])}), "
    f"el sunblotch ({pct(de_f['sunblotch']['tasa'][0])}) y la antracnosis ({pct(de_f['antracnosis_fruto']['tasa'][0])}). "
    f"En las hojas, la deficiencia nutricional fue detectada en el {pct(de_h['deficiencia_nutricional']['tasa'][0])} de los "
    f"casos, la antracnosis en el {pct(de_h['antracnosis_hoja']['tasa'][0])} y las plagas en el "
    f"{pct(de_h['plaga']['tasa'][0])}. Debido a que la antracnosis es la principal causa de descarte del fruto en "
    "poscosecha, su detección en hoja y en fruto resultó determinante para la prevención de pérdidas."))
add(parrafo(
    "Con el fin de aproximar la capacidad de detección temprana, se analizó la sensibilidad del sistema según el tamaño de "
    "la lesión, considerando que las lesiones de menor tamaño corresponden, por lo general, a estadios iniciales de la "
    "enfermedad. Se calculó el porcentaje de lesiones etiquetadas que fueron localizadas por el sistema con la clase correcta "
    "(IoU ≥ 0.50), agrupadas según la proporción del área de la imagen que ocupaban (Tabla 13)."))
t = next(T)
add(leyenda("Tabla", t, "Sensibilidad según el tamaño de la lesión"))
st_f, st_h = FR["sensibilidad_por_tamano"], HO["sensibilidad_por_tamano"]
fila = lambda d, k: (f"{d[k]['detectadas']} / {d[k]['total']}", pct(d[k]["tasa"][0]) if d[k]["total"] else "—")
filas = []
for k, et in (("pequena (<2%)", "Pequeña (< 2 %)"), ("mediana (2-10%)", "Mediana (2 % – 10 %)"), ("grande (>10%)", "Grande (> 10 %)")):
    a, b = fila(st_h, k); c, d = fila(st_f, k)
    filas.append([et, a, b, c, d])
add(tabla(["Tamaño de la lesión", "Hojas: detectadas / total", "Hojas: %", "Frutos: detectadas / total", "Frutos: %"],
          filas, [2400, 1900, 1100, 1900, 1100]))
add(nota("Elaboración propia. Tamaño expresado como proporción del área de la imagen ocupada por la caja delimitadora de "
         "la lesión. Se excluyeron las clases sanas."))
add(parrafo(
    f"Como se aprecia en la Tabla 13, la sensibilidad del sistema dependió del tamaño de la lesión: en los frutos, se "
    f"localizó el {pct(st_f['grande (>10%)']['tasa'][0])} de las lesiones grandes, el "
    f"{pct(st_f['mediana (2-10%)']['tasa'][0])} de las medianas y ninguna de las 17 lesiones pequeñas; en las hojas, se "
    f"localizó el {pct(st_h['grande (>10%)']['tasa'][0])} de las lesiones grandes y el "
    f"{pct(st_h['mediana (2-10%)']['tasa'][0])} de las medianas, aunque el conjunto de prueba de hojas no contuvo lesiones "
    "pequeñas y solo 14 medianas, por lo que este último valor debe interpretarse con cautela. Este resultado indicó que la detección temprana fue "
    "efectiva cuando la lesión ocupó una porción visible del órgano fotografiado, por lo que el protocolo de captura en "
    "campo debió privilegiar tomas cercanas que encuadren un solo fruto u hoja. La comparación del descarte antes y "
    "después de la implementación se presenta en la Tabla 14."))
t = next(T)
add(leyenda("Tabla", t, "Pérdidas por descarte antes y después de la implementación (resultados esperados por simulación)"))
de, pe = SIM["descarte"], SIM["perdida"]
add(tabla(["Indicador", "Preprueba", "Posprueba", "Diferencia", "Reducción (%)"], [
    ["Frutos descartados por daño fitosanitario (%)", ms(de, "pre"), ms(de, "post"), f"{de['dif']:.1f}", f"{de['reduccion'] * 100:.1f}"],
    ["Frutos descartados (n de 6,000 evaluados)", f"{tot['desc_pre']:,}", f"{tot['desc_post']:,}",
     f"{tot['desc_pre'] - tot['desc_post']:,}", f"{(1 - tot['desc_post'] / tot['desc_pre']) * 100:.1f}"],
    ["Frutos aptos sin daño fitosanitario (%)", f"{100 - de['media_pre']:.1f}", f"{100 - de['media_post']:.1f}",
     f"+{de['dif']:.1f}", "—"],
    ["Pérdida económica por árbol (S/)", ms(pe, "pre"), ms(pe, "post"), f"{pe['dif']:.2f}", f"{pe['reduccion'] * 100:.1f}"],
    ["Pérdida económica en la muestra (S/)", f"{tot['perdida_pre']:,.2f}", f"{tot['perdida_post']:,.2f}",
     f"{tot['perdida_pre'] - tot['perdida_post']:,.2f}", f"{(1 - tot['perdida_post'] / tot['perdida_pre']) * 100:.1f}"],
], [3100, 1450, 1450, 1250, 1250]))
add(nota("Elaboración propia. **Datos simulados** para 60 frutos evaluados por árbol en los 100 árboles de la muestra. "
         "Supuestos: descarte fitosanitario inicial de 14.5 % (sector A) y 16.0 % (sector B), reducción por detección "
         "temprana coherente con las tasas de detección de la Tabla 12, rendimiento de 24 kg por árbol y diferencia de "
         "S/ 3.80 por kilogramo entre el precio de exportación y el de mercado local. Estos valores serán reemplazados por "
         "los conteos registrados en campo en la tesis."))
add(parrafo(
    "Según los resultados esperados de la Tabla 14, la detección temprana de las enfermedades permitiría reducir el "
    f"porcentaje de frutos descartados por daño fitosanitario de {de['media_pre']:.1f} % a {de['media_post']:.1f} %, lo "
    f"que equivale a {tot['desc_pre'] - tot['desc_post']} frutos menos descartados en la muestra y a una disminución de "
    f"la pérdida económica de S/ {tot['perdida_pre']:,.2f} a S/ {tot['perdida_post']:,.2f} en los 100 árboles evaluados. "
    "La reducción esperada fue moderada, puesto que una parte del descarte obedece a daños que el sistema no detecta en "
    "estadios iniciales, como las lesiones pequeñas analizadas en la Tabla 13, y a factores ajenos a la sanidad del "
    "fruto."))

# ---------------------------------------------------------------- hipotesis
add(subtitulo("Contraste de hipótesis"))
add(parrafo(
    "Para la hipótesis específica 1 se contrastó si la exactitud diagnóstica del sistema superaba el umbral mínimo de "
    "desempeño del 70 % (H0: p ≤ 0.70; H1: p > 0.70) mediante la prueba binomial exacta unilateral, con un nivel de "
    "significancia de 0.05. Adicionalmente, se contrastó la exactitud frente a la meta de coincidencia del 85 % establecida "
    "en la matriz de operacionalización. Los resultados se presentan en la Tabla 15."))
t = next(T)
add(leyenda("Tabla", t, "Prueba binomial exacta de la exactitud diagnóstica"))
_P = {}


def _fila(nom, d):
    k, n = d["TP"] + d["TN"], d["n"]
    p70, p85 = binom_p(k, n, 0.70), binom_p(k, n, 0.85)
    _P[nom] = (p70, p85)
    dec = ("Se rechaza H0 en ambos umbrales" if p85 < 0.05 else "Se rechaza H0 solo para el 70 %") if p70 < 0.05 \
        else "No se rechaza H0"
    print("binomial", nom, k, n, p70, p85)
    return [nom, f"{k} / {n}", pct(d["exactitud"][0]), fp(p70), fp(p85), dec]



add(tabla(["Modelo", "Aciertos / n", "Exactitud", "p (H0: p ≤ 0.70)", "p (H0: p ≤ 0.85)", "Decisión"], [
    _fila("Hojas", hi), _fila("Frutos", fi),
], [1100, 1300, 1200, 1500, 1500, 2400]))
add(nota("Elaboración propia. Prueba binomial exacta unilateral (α = 0.05) sobre el split de prueba."))
add(parrafo(
    "Los resultados permitieron rechazar la hipótesis nula para el umbral del 70 % en ambos modelos (p < 0.001), con lo "
    "cual se aceptó la hipótesis específica 1: la implementación del sistema de visión computacional mejoró "
    "significativamente la precisión en el diagnóstico fitosanitario de la palta Hass, con un desempeño igual o superior "
    f"al 70 % en mAP50 (hojas: {pct(hj['mAP50'])}; frutos: {pct(fg['mAP50'])}). Respecto de la meta del 85 %, el modelo de "
    f"hojas la superó de forma significativa (p {'< 0.001' if _P['Hojas'][1] < 0.001 else '= ' + fp(_P['Hojas'][1])}), "
    f"mientras que en el modelo de frutos la diferencia no fue significativa (p = {fp(_P['Frutos'][1])})."))
add(parrafo(
    "Para las hipótesis específicas 2 y 3 se aplicó el procedimiento previsto sobre los datos simulados de preprueba y "
    "posprueba de los 100 árboles: la prueba de normalidad de Shapiro-Wilk a las diferencias pareadas y, según su "
    "resultado, la prueba t de Student para muestras relacionadas (diferencias normales, p > 0.05) o la prueba de rangos "
    "con signo de Wilcoxon (diferencias no normales), ambas unilaterales con α = 0.05 (H0: la media o mediana de la "
    "posprueba es mayor o igual que la de la preprueba). Los resultados se presentan en la Tabla 16."))
t = next(T)
add(leyenda("Tabla", t, "Contraste de las hipótesis específicas 2 y 3 (datos simulados)"))
f3 = lambda v: "< 0.001" if v < 0.001 else f"{v:.3f}"
filas = []
for h, k in (("HE2", "tiempo_arbol"), ("HE2", "tiempo_respuesta"), ("HE3", "descarte"), ("HE3", "perdida")):
    d = SIM[k]
    filas.append([h, d["variable"], f"{d['shapiro_W']:.3f} ({f3(d['shapiro_p'])})", d["prueba"],
                  f"{d['estadistico']:.2f}" if d["prueba"].startswith("t") else f"{d['estadistico']:.0f}",
                  f3(d["p"]), f"{d['efecto']} = {d['efecto_valor']:.2f}"])
add(tabla(["Hipótesis", "Variable", "Shapiro-Wilk W (p)", "Prueba", "Estadístico", "p", "Tamaño del efecto"], filas,
          [900, 2150, 1300, 1300, 1000, 1000, 1250], ["center", "left"] + ["center"] * 5))
add(nota("Elaboración propia. **Datos simulados** (n = 100 árboles). Pruebas unilaterales, α = 0.05. Tamaño del efecto: d de "
         "Cohen para la prueba t y r = Z/√n para la prueba de Wilcoxon."))
add(parrafo(
    "Con los datos simulados, en todos los casos se rechazó la hipótesis nula (p < 0.001). Para la hipótesis específica 2, "
    f"la reducción del tiempo de inspección por árbol presentó un tamaño del efecto grande (d = {ta['efecto_valor']:.2f}) y "
    f"la reducción del tiempo hasta el diagnóstico, también grande (r = {tr_['efecto_valor']:.2f}). Para la hipótesis "
    f"específica 3, la disminución del descarte y de la pérdida económica presentó un efecto moderado (d = "
    f"{de['efecto_valor']:.2f} y d = {pe['efecto_valor']:.2f}, respectivamente). En consecuencia, de confirmarse estos "
    "resultados con las mediciones de campo, se aceptarían las hipótesis específicas 2 y 3 y, junto con la hipótesis "
    "específica 1, la hipótesis general: la implementación del sistema de visión computacional mejora la producción de "
    "palta Hass en la localidad de Chao. Cabe precisar que el contraste de las hipótesis específicas 2 y 3 se presenta con "
    "fines demostrativos del procedimiento estadístico y será reemplazado por los datos de campo en la tesis."))

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
