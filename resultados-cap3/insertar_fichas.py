"""Inserta las Fichas 1 y 2 (ejemplo de llenado, datos simulados) como Anexos 7 y 8 al final del informe (v7 -> v8)."""
import re, shutil, zipfile
from pathlib import Path

S = Path(__file__).parent
SRC, DST = S / "work/v7", S / "work/v8"
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
doc = DST / "word/document.xml"
x = doc.read_text(encoding="utf8")

# ---------------------------------------------------------------- contenido de las fichas
z = zipfile.ZipFile("D:/AppWebPlagasPaltaHass/Fichas 1 y 2 - ejemplo de llenado (datos simulados).docx")
d = z.read("word/document.xml").decode("utf8")
body = d[d.index("<w:body>") + 8: d.rindex("<w:sectPr")]
# separar en las dos fichas por el parrafo que contiene el salto de seccion
corte = re.search(r"<w:p>(?:(?!</w:p>).)*?<w:sectPr.*?</w:p>|<w:p [^>]*>(?:(?!</w:p>).)*?<w:sectPr.*?</w:p>", body, re.S)
f1, f2 = body[:corte.start()], body[corte.end():]

FUENTE = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'


def limpiar(xml):
    # quitar "Anexo __" y el titulo en cursiva (el anexo lleva su propio titulo con campo SEQ)
    ps = re.findall(r"<w:p[ >].*?</w:p>|<w:tbl>.*?</w:tbl>", xml, re.S)
    out = []
    for blk in ps:
        t = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", blk))
        if blk.startswith("<w:p") and (t.startswith("Anexo __") or t.startswith("Ficha de observación tecnológica")):
            continue
        if blk.startswith("<w:p") and not t.strip() and "<w:sectPr" not in blk:   # espaciadores vacios
            continue
        out.append(blk)
    xml = "".join(out)

    # fuente TNR explicita en cada run
    def run(m):
        r = m.group(0)
        if "<w:rPr>" in r:
            return r.replace("<w:rPr>", "<w:rPr>" + FUENTE, 1)
        return r.replace("<w:r>", "<w:r><w:rPr>" + FUENTE + "</w:rPr>", 1)
    xml = re.sub(r"<w:r>.*?</w:r>", run, xml, flags=re.S)

    # neutralizar el estilo Normal de la tesis (sangria 709, espacio antes 240, interlineado 1.5)
    def par(m):
        p = m.group(0)
        if "<w:pPr>" not in p:
            p = re.sub(r"^(<w:p[^>]*>)", r"\1<w:pPr></w:pPr>", p)
        ppr = re.search(r"<w:pPr>(.*?)</w:pPr>", p, re.S)
        inner = ppr.group(1)
        after = re.search(r'w:after="(\d+)"', inner)
        ind = re.search(r"<w:ind [^>]*/>", inner)
        ind = ind.group(0) if ind else '<w:ind w:firstLine="0"/>'
        inner = re.sub(r"<w:spacing[^>]*/>|<w:ind [^>]*/>", "", inner)
        sp = f'<w:spacing w:before="0" w:after="{after.group(1) if after else 0}" w:line="240" w:lineRule="auto"/>'
        # orden del esquema: ... spacing, ind, jc, textDirection, rPr, sectPr
        ks = [inner.find(t) for t in ("<w:jc ", "<w:textDirection", "<w:rPr>", "<w:sectPr") if inner.find(t) >= 0]
        k = min(ks) if ks else len(inner)
        inner = inner[:k] + sp + ind + inner[k:]
        return p[:ppr.start()] + "<w:pPr>" + inner + "</w:pPr>" + p[ppr.end():]
    xml = re.sub(r"<w:p[ >](?:(?!<w:p[ >]).)*?</w:p>", par, xml, flags=re.S)

    # orden del esquema en tcPr: tcW, gridSpan, vMerge, tcBorders, shd, ..., vAlign
    ORDEN = ["tcW", "gridSpan", "vMerge", "tcBorders", "shd", "noWrap", "tcMar", "textDirection", "tcFitText", "vAlign"]
    def tcpr(m):
        partes = re.findall(r"(<w:(\w+)(?:[^>]*/>|[^>]*>.*?</w:\2>))", m.group(1), re.S)
        partes.sort(key=lambda t: ORDEN.index(t[1]) if t[1] in ORDEN else 99)
        return "<w:tcPr>" + "".join(t[0] for t in partes) + "</w:tcPr>"
    xml = re.sub(r"<w:tcPr>(.*?)</w:tcPr>", tcpr, xml, flags=re.S)
    def bordes(m):
        el = dict(re.findall(r"(<w:(top|left|bottom|right)[^>]*/>)", m.group(1))[::-1] and
                  [(k, v) for v, k in re.findall(r"(<w:(top|left|bottom|right)[^>]*/>)", m.group(1))])
        return "<w:tcBorders>" + "".join(el[k] for k in ("top", "left", "bottom", "right") if k in el) + "</w:tcBorders>"
    xml = re.sub(r"<w:tcBorders>(.*?)</w:tcBorders>", bordes, xml, flags=re.S)
    # compactar filas para que cada ficha quepa en una pagina con el encabezado de la tesis
    xml = re.sub(r'(<w:trHeight [^>]*w:val=")(\d+)(")', lambda m: m.group(1) + str(int(int(m.group(2)) * 0.78)) + m.group(3), xml)
    return xml


def titulo(n, texto):
    """Mismo formato que los anexos de la tesis: estilo Descripcion + campo SEQ Anexo."""
    rb = '<w:rPr><w:b/><w:bCs/><w:i w:val="0"/><w:iCs w:val="0"/><w:color w:val="000000" w:themeColor="text1"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>'
    rn = '<w:rPr><w:color w:val="000000" w:themeColor="text1"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>'
    return (f'<w:p><w:pPr><w:pStyle w:val="Descripcin"/><w:keepNext/><w:spacing w:line="360" w:lineRule="auto"/>'
            f'<w:ind w:firstLine="0"/></w:pPr><w:r>{rb}<w:t xml:space="preserve">Anexo </w:t><w:fldChar w:fldCharType="begin"/>'
            f'<w:instrText xml:space="preserve"> SEQ Anexo \\* ARABIC </w:instrText><w:fldChar w:fldCharType="separate"/>'
            f'<w:t>{n}</w:t><w:fldChar w:fldCharType="end"/><w:t xml:space="preserve"> </w:t><w:br/></w:r>'
            f'<w:r>{rn}<w:t>{texto}</w:t></w:r></w:p>')


final = x[x.rindex("<w:sectPr"): x.rindex("</w:body>")]
vertical = final                                            # cierra la seccion vertical de la tesis
horiz = (final.replace('<w:type w:val="continuous"/>', '<w:type w:val="nextPage"/>')
         .replace('<w:pgSz w:w="11906" w:h="16838" w:code="9"/>', '<w:pgSz w:w="16838" w:h="11906" w:orient="landscape" w:code="9"/>')
         .replace('w:top="1418" w:right="1701" w:bottom="1418" w:left="1701"', 'w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"'))
assert horiz != final and 'orient="landscape"' in horiz

nuevo = (f"<w:p><w:pPr>{vertical}</w:pPr></w:p>"
         + titulo(7, "Ficha de observación tecnológica N.° 1: tiempo de inspección manual (preprueba). Ejemplo de llenado con datos simulados")
         + limpiar(f1) + '<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="120" w:lineRule="exact"/><w:ind w:firstLine="0"/></w:pPr></w:p>'
         + f"<w:p><w:pPr>{horiz}</w:pPr></w:p>"
         + titulo(8, "Ficha de observación tecnológica N.° 2: inspección con el sistema de visión computacional (posprueba). Ejemplo de llenado con datos simulados")
         + limpiar(f2) + '<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="120" w:lineRule="exact"/><w:ind w:firstLine="0"/></w:pPr></w:p>')
i = x.rindex("<w:sectPr")
x = x[:i] + nuevo + horiz + x[x.rindex("</w:body>"):]
doc.write_text(x, encoding="utf8")

out = S / "work/v8.docx"
out.unlink(missing_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zz:
    zz.write(DST / "[Content_Types].xml", "[Content_Types].xml")
    for f in sorted(DST.rglob("*")):
        if f.is_file() and f.name != "[Content_Types].xml":
            zz.write(f, f.relative_to(DST).as_posix())
print("ok", out)
