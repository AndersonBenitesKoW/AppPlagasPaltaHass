"""Correcciones de coherencia de los Cap. I y II y alineacion del Anexo 2 (cambios controlados) -> v9."""
import re
import sys
from pathlib import Path

S = Path(__file__).parent
src = (S / "edit_cap1.py").read_text(encoding="utf8")
helpers = src[:src.index("d = Doc(open(DOC")]
sys.argv = ["x", str(S / "work/v9/word/document.xml")]
exec(helpers)
FECHA = "2026-10-22T00:00:00Z"

d = Doc(open(DOC, encoding="utf8").read())
hechos = []


def cambiar(ancla, viejo, nuevo, n=0):
    """Reemplazo controlado; si el fragmento no esta en un solo run, se reescribe el parrafo."""
    try:
        d.sustituir(ancla, viejo, nuevo, n)
    except SystemExit as e:
        if "NO ENCONTRADO" in str(e):
            raise
        ini, fin, p = d.buscar(ancla, n)
        t = txt(p)
        assert viejo in t, viejo
        d.reemplazar_parrafo(ancla, t.replace(viejo, nuevo), n)
    hechos.append(viejo[:60])


def celda(viejo, nuevo):
    d.reemplazar_parrafo(viejo, nuevo)
    hechos.append(viejo[:60])


# ============================================================== CAP. I
cambiar("tres departamentos concentraron", "112,9%", "112.9 %")
cambiar("tres departamentos concentraron", "83,7%", "83.7 %")
cambiar("La carencia de automatización", "y la correcta proyección de cosecha",
        "y la detección oportuna de las enfermedades en hojas y frutos")
cambiar("Entre los factores que limitan", "el error humano en el conteo manual",
        "el error humano en la inspección visual manual")
cambiar("Entre los factores que limitan", "dejar pasar frutos enfermos, manchas, deformidades o realizar conteos inexactos de la palta Hass",
        "dejar pasar hojas y frutos enfermos, no advertir manchas o lesiones en sus etapas iniciales o diagnosticar tardíamente las enfermedades de la palta Hass")
cambiar("fruitlets", "93,8%", "93.8 %")
cambiar("fruitlets", "validando su uso para sistemas de estimación de rendimiento agrícola en tiempo real.",
        "validando su uso para la detección en tiempo real de afecciones en hojas y frutos, como se plantea en la presente investigación.")
cambiar("Acuña Chumpitazi y Tito Vargas (2023) desarrollaron", "Finalmente, Acuña Chumpitazi", "Del mismo modo, Acuña Chumpitazi")
cambiar("optimiza la producción de palta Hass en la localidad de Chao, provincia de Virú, región La Libertad, 2026?",
        "¿En qué medida", "¿De qué manera")

# ============================================================== CAP. II
# Poblacion: criterios duplicados, numero de tabla y estilo del parrafo
pob = "La unidad de estudio de la presente investigación"
ini, fin, p = d.buscar(pob)
t = txt(p)
k1 = t.index("Se consideraron como criterios de inclusión")
k2 = t.index("Para fines experimentales")
nuevo = t[:k1] + t[k2:]
nuevo = nuevo.replace("se detalla en la Tabla 2:", "se detalla en la Tabla 1:")
d.reemplazar_parrafo(pob, nuevo, rpr="")
ini, fin, p = d.buscar(pob)
viejo_ppr = re.search(r"<w:pPr>(.*?)</w:pPr>", p, re.S)
cambio = (f'<w:pPrChange w:id="{nid()}" w:author="{AUTOR}" w:date="{FECHA}"><w:pPr>'
          + re.sub(r"<w:rPr>.*?</w:rPr>", "", viejo_ppr.group(1), flags=re.S) + "</w:pPr></w:pPrChange>")
nuevo_ppr = '<w:pPr><w:pStyle w:val="APA7"/>' + cambio + "</w:pPr>"
d._set(ini, fin, p[:viejo_ppr.start()] + nuevo_ppr + p[viejo_ppr.end():])
hechos.append("poblacion: criterios duplicados, Tabla 2->1, estilo APA7")

cambiar("cuyo cálculo matemático resultó", "(e = 0.10$)", "(e = 0.10)")
cambiar("La adopción de un margen de error del 10%",
        "en primer lugar, la unidad de medición efectiva del rendimiento del modelo no es el árbol en sí, sino la imagen digital capturada, ya que al registrarse aproximadamente diez tomas fotográficas por espécimen entre hojas y frutos, la muestra de 100 árboles genera un banco cercano a 1,000 imágenes etiquetadas, volumen suficiente para estimar con estabilidad las métricas de Precisión, Recall y mAP de la arquitectura de aprendizaje profundo.",
        "en primer lugar, la unidad de medición efectiva del rendimiento del modelo no es el árbol en sí, sino la imagen digital: las métricas de Precisión, Recall y mAP se estiman sobre el conjunto de prueba del dataset curado (618 imágenes con 811 instancias etiquetadas, independientes del entrenamiento), mientras que las diez tomas fotográficas por árbol (cinco hojas y cinco frutos), que suman cerca de 1,000 imágenes de campo, permiten verificar el desempeño del sistema en condiciones reales y su concordancia con el diagnóstico del especialista.")
cambiar("La adopción de un margen de error del 10%",
        "de modo que el contraste estadístico se ejecuta sobre 200 mediciones y no sobre 100, lo que conserva una potencia estadística adecuada para detectar efectos de magnitud media con un nivel de significancia del 5% (Hernández Sampieri et al., 2014).",
        "y el contraste estadístico se realiza sobre las 100 diferencias pareadas; con este tamaño, la prueba para muestras relacionadas conserva una potencia superior a 0.95 para detectar efectos de magnitud media (d = 0.5) con un nivel de significancia del 5 % (Hernández Sampieri et al., 2014).")

# tecnica: entrevista -> encuesta (Figura 1, texto y Tabla 2)
celda("-Entrevista agropecuaria", "-Encuesta al personal del huerto (cuestionario)")
celda("Entrevista Agropecuaria", "Encuesta")
cambiar("Para garantizar la calidad, objetividad y confiabilidad",
        "y la entrevista agropecuaria dirigida a los expertos del huerto para evaluar las variables operativas y de producción.",
        "y la encuesta, mediante un cuestionario dirigido al personal técnico y a los especialistas del huerto, para evaluar el control fitosanitario y la reducción del descarte.")

# analisis: tiempos verbales y software
an = "El análisis se dividió en dos fases principales"
for v, n_ in [("los datos tabulados se analizarán", "los datos tabulados se analizaron"),
              ("que determinarán la viabilidad técnica", "que determinaron la viabilidad técnica"),
              ("asimismo, se aplicará estadística descriptiva", "asimismo, se aplicó estadística descriptiva"),
              ("utilizando un software estadístico (como SPSS o lenguaje R)", "utilizando el lenguaje Python (librerías Ultralytics y SciPy)"),
              ("se ejecutará una prueba de normalidad", "se ejecutó una prueba de normalidad"),
              ("se utilizará la prueba paramétrica", "se utilizó la prueba paramétrica"),
              ("se aplicará la prueba no paramétrica", "se aplicó la prueba no paramétrica")]:
    cambiar(an, v, n_)

# aspectos eticos
et = "La presente investigación se desarrolló conforme a los principios éticos"
cambiar(et, "y destruidos de manera segura una vez concluido el análisis y la presentación de los resultados",
        "y conservados únicamente durante el periodo que establece la universidad, tras el cual serán eliminados de forma segura")
cambiar(et, "lineamientos de investigación de la universidad..", "lineamientos de investigación de la universidad.")

# ============================================================== ANEXO 2 (operacionalizacion)
celda("Modelo de red neuronal convolucional entrenado",
      "Modelos de detección de objetos YOLO11, basados en redes neuronales convolucionales, entrenados con un dataset "
      "fitosanitario de imágenes de hojas (cuatro clases) y frutos (seis clases) de palta Hass y evaluados mediante métricas "
      "estandarizadas sobre un conjunto de prueba independiente. El sistema se implementa como aplicación web en campo y sus "
      "resultados se contrastan con la inspección manual tradicional.")
celda("Medición cronométrica del tiempo de inferencia",
      "Medición del tiempo de procesamiento por imagen (lectura, preprocesamiento, inferencia y posprocesamiento) sobre el "
      "conjunto de prueba y durante las pruebas en campo.")
celda("Tiempo de inferencia por imagen",
      "Tiempo de procesamiento por imagen (ms), imágenes procesadas por minuto.")
celda("Tiempo promedio en milisegundos",
      "Tiempo promedio en milisegundos. Óptimo si ≤ 150 ms por imagen en el modo de tiempo real (modelo de hojas) y "
      "aceptable si ≤ 1,000 ms en el análisis por imagen en el servidor (modelo de frutos).")
celda("Evaluación del porcentaje de aciertos",
      "Porcentaje de imágenes con una afección en las que el sistema detecta dicha afección y sensibilidad según el tamaño de "
      "la lesión, contrastados con el etiquetado de referencia y con el diagnóstico de un especialista.")
celda("Tasa de verdaderos positivos",
      "Sensibilidad o tasa de verdaderos positivos (TPR) a nivel de imagen, tasa de falsos negativos (FNR), tasa de detección "
      "por enfermedad, sensibilidad según el tamaño de la lesión.")
celda("Comparación de los resultados del sistema",
      "Comparación de los resultados del sistema con el etiquetado de referencia del conjunto de prueba y con el diagnóstico "
      "de un ingeniero agrónomo experto, calculando la exactitud, la concordancia y los errores de clasificación.")
celda("% de coincidencia con el diagnóstico",
      "Exactitud diagnóstica, sensibilidad, especificidad, coeficiente kappa de Cohen, % de coincidencia con el diagnóstico "
      "experto, número de falsos positivos y falsos negativos.")
celda("Porcentaje de coincidencia (0%",
      "Porcentaje de exactitud y de coincidencia (0 % – 100 %). Se considera aceptable si ≥ 85 %.")
celda("Registro cronométrico del tiempo empleado",
      "Registro cronométrico del tiempo de inspección por árbol y del tiempo transcurrido desde la detección del síntoma hasta "
      "el diagnóstico, tanto en la preprueba (inspección manual) como en la posprueba (con el sistema).")
celda("Tiempo promedio de inspección por árbol (min), tiempo total",
      "Tiempo promedio de inspección por árbol (min), tiempo desde la detección del síntoma hasta el diagnóstico (h), tiempo "
      "estimado de inspección por hectárea (h).")
celda("Se espera una reducción ≥ 50%",
      "Tiempo promedio en minutos. Se espera una reducción ≥ 30 % respecto al método manual.")
celda("Registro de la cantidad de frutos descartados",
      "Registro de la cantidad de frutos descartados por daño fitosanitario y de frutos aptos en una muestra de 60 frutos por "
      "árbol, en la preprueba y en la posprueba, calculando la reducción porcentual.")
celda("% de frutos descartados, % de frutos",
      "% de frutos descartados por daño fitosanitario, % de frutos aptos, pérdida económica estimada (S/ por árbol y en la "
      "muestra).")
celda("Se espera una reducción ≥ 30%",
      "Porcentaje de descarte. Se espera una reducción ≥ 15 % respecto a la preprueba.")

open(DOC, "w", encoding="utf8").write(d.xml)
print(len(hechos), "cambios")
