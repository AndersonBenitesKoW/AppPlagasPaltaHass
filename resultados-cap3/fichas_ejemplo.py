"""Ejemplo de llenado de las Fichas 1 y 2 con los datos SIMULADOS del Cap. III (arboles A-01 a A-08)."""
from pathlib import Path
import numpy as np
from openpyxl import load_workbook

S = Path(__file__).parent
src = (S / "fichas.py").read_text(encoding="utf8")
exec(src[:src.index("# =====================================================================================  PROTOCOLO")])

from docx.shared import Pt, RGBColor

MARCA = "EJEMPLO DE LLENADO – DATOS SIMULADOS (no corresponde a mediciones de campo)"
ws = load_workbook(S / "datos_simulados_campo.xlsx")["datos_simulados"]
filas = [r for r in ws.iter_rows(min_row=2, max_row=9, values_only=True)]
rng = np.random.default_rng(7)
DX = [("S", None), ("AH", "AH 78.4 %"), ("S", None), ("AF", "AF 81.3 %"), ("PL", "PL 64.2 %"), ("S", None),
      ("AF, RO", "AF 86.0 %; RO 58.7 %"), ("DN", "DN 91.5 %")]
SANO_CONF = ["S 88.1 %", "S 92.4 %", "S 85.6 %"]


def hhmmss(seg):
    seg = int(round(seg))
    return f"{seg // 3600:02d}:{seg % 3600 // 60:02d}:{seg % 60:02d}"


def marca():
    par = p(MARCA, negrita=True, centro=True, doble=False, size=10, after=4)
    for r in par.runs:
        r.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)


def gen(etapa):
    return [("Fundo / unidad agrícola:", "Fundo de palta Hass (ejemplo)   Localidad: Chao, Virú, La Libertad"),
            ("Sector:", "☒ A     ☐ B          Fecha: 03 / 11 / 2026"),
            ("Etapa:", "☒ Preprueba (sin sistema)     ☐ Posprueba (con sistema)" if etapa == "pre"
             else "☐ Preprueba (sin sistema)     ☒ Posprueba (con sistema)"),
            ("Evaluador:", "Técnico de campo (ejemplo)   Cargo: Técnico agrícola"),
            ("Condición del día:", "☒ Soleado   ☐ Nublado   ☐ Garúa      Hora de inicio de jornada: 08:00"),
            ("Hoja N.°:", "1 de 13")]


# ---------------- Ficha 1
for s in doc.sections:
    s.orientation = WD_ORIENT.LANDSCAPE
    s.page_width, s.page_height = Cm(29.7), Cm(21)
    s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(2.0)
marca()
titulo_instr("__", "Ficha de observación tecnológica N.° 1: Tiempo de inspección manual (preprueba) – ejemplo de llenado")
campos(gen("pre"), (5.0, 20.5))
p("", doble=False, after=6)
t = 8 * 3600
f1 = []
for i, r in enumerate(filas):
    cod, sec, tpre, tpost, rpre, rpost = r[:6]
    ini = t; fin = t + tpre * 60; t = fin + rng.uniform(60, 150)          # traslado al siguiente arbol
    av_h = next(h / 4 for h in range(26, 74) if 7.5 <= (h / 4 + rpre) % 24 <= 17.5)   # aviso y diagnostico en horario laboral
    aviso = f"{(i % 3) + 27}/10 {int(av_h):02d}:{int(av_h % 1 * 60):02d}"
    diag_t = av_h + rpre
    dia = (i % 3) + 27 + int(diag_t // 24)
    dmes = f"{dia}/10" if dia <= 31 else f"{dia - 31:02d}/11"
    diag = f"{dmes} {int(diag_t % 24):02d}:{int((diag_t % 1) * 60) + 0:02d}"
    f1.append([str(i + 1), cod, hhmmss(ini), hhmmss(fin), f"{tpre:.1f}", "5", "5", DX[i][0], aviso, diag,
               f"{rpre:.1f}", "Copa densa" if tpre > 8.5 else ""])
tabla(["N.°", "Código del árbol", "Hora de inicio (hh:mm:ss)", "Hora de fin (hh:mm:ss)", "Duración (min)",
       "Hojas revisadas (n)", "Frutos revisados (n)", "Diagnóstico visual del técnico",
       "Fecha y hora del aviso del síntoma", "Fecha y hora del diagnóstico", "Tiempo hasta el diagnóstico (h)",
       "Observaciones"], f1, [0.8, 1.8, 2.0, 2.0, 1.6, 1.6, 1.6, 4.0, 2.6, 2.6, 2.0, 3.1], size=8, alto=0.75)
p("Diagnóstico visual: S = sano; AH = antracnosis en hoja; PL = plagas (trips/ácaros); DN = deficiencia nutricional; "
  "AF = antracnosis en fruto; CE = cercospora; RO = roña; PP = pudrición peduncular; SB = sunblotch.", doble=False, size=9)
firmas(["Evaluador (técnico)", "Responsable de la investigación"])

# ---------------- Ficha 2
nueva_seccion(True)
marca()
titulo_instr("__", "Ficha de observación tecnológica N.° 2: Inspección con el sistema (posprueba) – ejemplo de llenado")
g = gen("post"); g[1] = ("Sector:", "☒ A     ☐ B          Fecha: 24 / 11 / 2026")
campos(g[:2] + g[3:], (5.0, 20.5))
p("", doble=False, after=6)
t = 8 * 3600
f2 = []
for i, r in enumerate(filas):
    cod, sec, tpre, tpost, rpre, rpost = r[:6]
    ini = t; fin = t + tpost * 60; t = fin + rng.uniform(60, 150)
    envio = fin + 30
    conf = envio + rpost * 3600
    sistema = DX[i][1] or SANO_CONF[i % 3]
    ver = "Sano" if DX[i][1] is None else "Alerta"
    f2.append([str(i + 1), cod, hhmmss(ini)[:5], hhmmss(fin)[:5], f"{tpost:.1f}", "5", "5",
               f"INS-{1001 + i * 10}…{1010 + i * 10}", sistema, ver,
               hhmmss(envio)[:5], (hhmmss(conf % 86400)[:5] + (" (+1 d)" if conf >= 86400 else "")), f"{rpost:.1f}", ""])
tabla(["N.°", "Código del árbol", "Hora de inicio", "Hora de fin", "Duración (min)", "Imágenes de hojas (n)",
       "Imágenes de frutos (n)", "Código(s) de inspección en el sistema", "Diagnóstico del sistema (clase y confianza)",
       "Veredicto (sano / alerta)", "Hora de envío al técnico", "Hora de confirmación", "Tiempo hasta el diagnóstico (h)",
       "Observaciones"], f2, [0.8, 1.6, 1.5, 1.5, 1.4, 1.4, 1.4, 2.4, 3.4, 1.6, 1.6, 1.6, 1.7, 2.4], size=8, alto=0.75)
p("Datos tomados de la simulación del Cap. III (archivo datos_simulados_campo.xlsx, árboles A-01 a A-08). En la "
  "aplicación real, este formato se completa con los registros de campo.", doble=False, size=9)
firmas(["Evaluador (técnico)", "Responsable de la investigación"])

f = Path("D:/AppWebPlagasPaltaHass/Fichas 1 y 2 - ejemplo de llenado (datos simulados).docx")
doc.save(f)
print(f)
for x in f1: print(x[1], x[8], x[9], x[10])
for x in f2: print(x[1], x[4], x[8], x[12])
