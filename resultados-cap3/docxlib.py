"""Helpers para generar XML de Word clonando el formato de la tesis (APA7, TNR 12, tablas APA)."""
import re, shutil, struct
from pathlib import Path
from xml.sax.saxutils import escape

_pid = [0x5A000000]


def _id():
    _pid[0] += 1
    return f'w14:paraId="{_pid[0]:08X}" w14:textId="77777777"'


def _ins(base, extra):
    """Inserta b/i despues de rFonts para respetar el orden del esquema de rPr."""
    m = re.match(r"(<w:rFonts[^>]*/>)?(.*)", base, re.S)
    return (m.group(1) or "") + extra + m.group(2)


def runs(texto, base=""):
    """Convierte **negrita** y _cursiva_ en runs."""
    out = []
    for tok in re.split(r"(\*\*[^*]+\*\*|__[^_]+__|\[\[[^\]]+\]\])", texto):
        if not tok:
            continue
        rpr = base
        if tok.startswith("[["):
            tok, rpr = tok[2:-2], base + '<w:highlight w:val="yellow"/>'
        elif tok.startswith("**"):
            tok, rpr = tok[2:-2], _ins(base, "<w:b/><w:bCs/>")
        elif tok.startswith("__"):
            tok, rpr = tok[2:-2], _ins(base, "<w:i/><w:iCs/>")
        r = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
        out.append(f'<w:r>{r}<w:t xml:space="preserve">{escape(tok)}</w:t></w:r>')
    return "".join(out)


def parrafo(texto):
    return f'<w:p {_id()}><w:pPr><w:pStyle w:val="APA7"/></w:pPr>{runs(texto)}</w:p>'


def subtitulo(texto):
    return (f'<w:p {_id()}><w:pPr><w:pStyle w:val="APA7"/><w:rPr><w:b/><w:bCs/></w:rPr></w:pPr>'
            f'<w:r><w:rPr><w:b/><w:bCs/></w:rPr><w:t xml:space="preserve">{escape(texto)}</w:t></w:r></w:p>')


def nota(texto):
    rpr = '<w:rFonts w:cs="Times New Roman"/><w:sz w:val="20"/><w:szCs w:val="20"/>'
    return (f'<w:p {_id()}><w:pPr><w:pStyle w:val="APA7"/><w:spacing w:before="60" w:after="240" w:line="240" w:lineRule="auto"/>'
            f'<w:ind w:firstLine="0"/><w:rPr>{rpr}</w:rPr></w:pPr>'
            f'<w:r><w:rPr>{_ins(rpr, "<w:i/><w:iCs/>")}</w:rPr><w:t xml:space="preserve">Nota. </w:t></w:r>{runs(texto, rpr)}</w:p>')


def leyenda(tipo, n, titulo):
    """tipo: 'Tabla' (estilo TABLA0) o 'Figura' (estilo FIGURA0); numeracion con campo SEQ como en la tesis."""
    st = "TABLA0" if tipo == "Tabla" else "FIGURA0"
    return (f'<w:p {_id()}><w:pPr><w:pStyle w:val="{st}"/><w:keepNext/><w:keepLines/></w:pPr>'
            f'<w:r><w:t xml:space="preserve">{tipo} </w:t><w:fldChar w:fldCharType="begin"/>'
            f'<w:instrText xml:space="preserve"> SEQ {tipo} \\* ARABIC </w:instrText><w:fldChar w:fldCharType="separate"/></w:r>'
            f'<w:r><w:rPr><w:noProof/></w:rPr><w:t>{n}</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/><w:br/></w:r>'
            f'<w:r><w:rPr><w:b w:val="0"/><w:bCs w:val="0"/><w:i/><w:iCs/></w:rPr><w:t xml:space="preserve">{escape(titulo)}</w:t></w:r></w:p>')


def _celda(texto, ancho, top, bottom, alin="center", negrita=False, junto=True):
    b = lambda v: '<w:{0} w:val="single" w:sz="4" w:space="0" w:color="auto"/>' if v else '<w:{0} w:val="nil"/>'
    bord = (b(top).format("top") + '<w:left w:val="nil"/>' + b(bottom).format("bottom") + '<w:right w:val="nil"/>')
    rpr = '<w:rFonts w:cs="Times New Roman"/>' + ("<w:b/><w:bCs/>" if negrita else "") + '<w:sz w:val="20"/><w:szCs w:val="20"/>'
    jc = f'<w:jc w:val="{alin}"/>'
    return (f'<w:tc><w:tcPr><w:tcW w:w="{ancho}" w:type="dxa"/><w:tcBorders>{bord}</w:tcBorders><w:vAlign w:val="center"/></w:tcPr>'
            f'<w:p {_id()}><w:pPr>' + ('<w:keepNext/>' if junto else '') + '<w:widowControl/><w:autoSpaceDE/><w:autoSpaceDN/>'
            f'<w:spacing w:before="40" w:after="40" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/>{jc}'
            f'<w:rPr>{rpr}</w:rPr></w:pPr>{runs(str(texto), rpr)}</w:p></w:tc>')


def tabla(cab, filas, anchos, alin=None, total=False):
    """Tabla estilo APA: linea superior e inferior del encabezado y linea final; sin lineas verticales."""
    alin = alin or ["left"] + ["center"] * (len(cab) - 1)
    g = "".join(f'<w:gridCol w:w="{a}"/>' for a in anchos)
    x = [f'<w:tbl><w:tblPr><w:tblStyle w:val="Tablaconcuadrcula"/><w:tblW w:w="0" w:type="auto"/><w:jc w:val="center"/>'
         f'<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
         f'</w:tblPr><w:tblGrid>{g}</w:tblGrid>']
    x.append('<w:tr><w:trPr><w:tblHeader/><w:jc w:val="center"/></w:trPr>' +
             "".join(_celda(c, a, True, True, "center") for c, a in zip(cab, anchos)) + "</w:tr>")
    for i, f in enumerate(filas):
        ult = i == len(filas) - 1
        neg = total and ult
        top = total and ult
        x.append('<w:tr><w:trPr><w:cantSplit/><w:jc w:val="center"/></w:trPr>' +
                 "".join(_celda(c, a, top, ult, al, neg, not ult) for c, a, al in zip(f, anchos, alin)) + "</w:tr>")
    x.append("</w:tbl>")
    return "".join(x)


def _png_size(p):
    d = Path(p).read_bytes()[:24]
    return struct.unpack(">II", d[16:24])


class Imagenes:
    def __init__(self, unpacked):
        self.u = Path(unpacked)
        self.rels = self.u / "word/_rels/document.xml.rels"
        self.n = 0

    def drawing(self, png, ancho_cm=15.0, desc="Figura"):
        txt = self.rels.read_text(encoding="utf8")
        self.n += 1
        nombre = f"cap3_fig{self.n}.png"
        shutil.copy(png, self.u / "word/media" / nombre)
        rid = f"rIdCap3Img{self.n}"
        txt = txt.replace("</Relationships>",
                          f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{nombre}"/></Relationships>')
        self.rels.write_text(txt, encoding="utf8")
        w, h = _png_size(png)
        cx = int(ancho_cm * 360000)
        cy = int(cx * h / w)
        did = 880000 + self.n
        return (f'<w:p {_id()}><w:pPr><w:pStyle w:val="APA7"/><w:keepNext/><w:ind w:firstLine="0"/><w:jc w:val="center"/></w:pPr>'
                f'<w:r><w:rPr><w:noProof/></w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
                f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
                f'<wp:docPr id="{did}" name="Imagen {did}" descr="{escape(desc)}"/>'
                f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
                f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{did}" name="{nombre}"/><pic:cNvPicPr/></pic:nvPicPr>'
                f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
                f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')
