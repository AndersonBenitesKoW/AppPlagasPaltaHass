"""Genera revision/galeria_fruto_sano.html para revisar a mano las imagenes de 'fruto_sano'.

Ordena las imagenes por un puntaje de "oscuridad" (proporcion de pixeles oscuros o no verdes
dentro de las cajas de fruto sano) para que las sospechosas aparezcan primero. En la galeria se
marcan las imagenes a excluir y se descarga 'excluir_fruto_sano.txt', que se guarda en revision/.

Uso:  python scripts/01_galeria_fruto_sano.py
"""
import html
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from comun import CLASES_ORIGINALES, REVISION, cargar_imagenes, mapear

UMBRAL_SUGERIDO = 0.5    # puntaje a partir del cual la imagen se marca como "sugerida" (no se excluye sola)
LADO_MINIATURA = 300


def puntaje_oscuridad(img, cajas):
    """Maximo, entre los frutos sanos de la imagen, de la fraccion de pixeles oscuros o no verdes."""
    W, H = img.size
    hsv = img.convert("HSV")
    peor = 0.0
    for xc, yc, w, h in cajas:
        recorte = hsv.crop((int((xc - w / 2) * W), int((yc - h / 2) * H),
                            int((xc + w / 2) * W), int((yc + h / 2) * H))).resize((64, 64))
        a = np.asarray(recorte, dtype=np.int16)
        hue, sat, val = a[..., 0], a[..., 1], a[..., 2]
        contenido = ~(((sat < 30) & (val > 200)) | (val < 15))   # ignora fondo blanco/gris y relleno negro
        if contenido.sum() < 50:
            continue
        oscuro = val < 70
        no_verde = (sat > 50) & ((hue < 35) | (hue > 130))       # marron, rojo, morado (hue PIL 0-255)
        peor = max(peor, float(((oscuro | no_verde) & contenido).sum() / contenido.sum()))
    return peor


def main():
    carpeta_mini = REVISION / "galeria_fruto_sano"
    carpeta_mini.mkdir(parents=True, exist_ok=True)

    items = []
    for im in cargar_imagenes():
        sanas = [a for a in im["anotaciones"] if mapear(a["clase"], a["poligono"]) == ("frutos", "fruto_sano")]
        if not sanas:
            continue
        img = Image.open(im["imagen"]).convert("RGB")
        cajas = [a["caja"] for a in sanas]
        puntaje = puntaje_oscuridad(img, cajas)

        # Los otros frutos de la foto tienen su propia etiqueta de enfermedad (no los afecta la revision):
        # se dibujan en rojo con su nombre para no confundirlos con frutos sanos mal etiquetados.
        otras = [(mapear(a["clase"], a["poligono"])[1], a["caja"]) for a in im["anotaciones"]
                 if mapear(a["clase"], a["poligono"]) not in (None, ("frutos", "fruto_sano"))]

        W, H = img.size
        grosor = max(3, W // 200)
        dibujo = ImageDraw.Draw(img)
        fuente = ImageFont.load_default(size=max(14, W // 30))
        for nombre, (xc, yc, w, h) in otras:
            x1, y1 = (xc - w / 2) * W, (yc - h / 2) * H
            dibujo.rectangle([x1, y1, (xc + w / 2) * W, (yc + h / 2) * H], outline=(230, 40, 40), width=grosor)
            dibujo.text((x1 + grosor, y1 + grosor), nombre, fill=(255, 255, 255), font=fuente,
                        stroke_width=2, stroke_fill=(230, 40, 40))
        for xc, yc, w, h in cajas:
            dibujo.rectangle([(xc - w / 2) * W, (yc - h / 2) * H, (xc + w / 2) * W, (yc + h / 2) * H],
                             outline=(0, 255, 0), width=grosor)
        nombre_mini = im["id"].replace("/", "__") + ".jpg"
        img.thumbnail((LADO_MINIATURA, LADO_MINIATURA))
        img.save(carpeta_mini / nombre_mini, quality=75)

        origen = sorted({CLASES_ORIGINALES[a["clase"]] + (" (polígono)" if a["poligono"] else " (caja)") for a in sanas})
        items.append({
            "id": im["id"],
            "mini": f"galeria_fruto_sano/{nombre_mini}",
            "original": "../DatasetOriginal/" + im["split"] + "/images/" + im["imagen"].name,
            "puntaje": round(puntaje, 3),
            "origen": ", ".join(origen),
            "frutos": len(cajas),
            "otras": ", ".join(sorted({n for n, _ in otras})),
        })

    items.sort(key=lambda x: -x["puntaje"])
    pagina = PLANTILLA.replace("__DATOS__", json.dumps(items)).replace("__UMBRAL__", str(UMBRAL_SUGERIDO))
    salida = REVISION / "galeria_fruto_sano.html"
    salida.write_text(pagina, encoding="utf-8")
    sugeridas = sum(x["puntaje"] >= UMBRAL_SUGERIDO for x in items)
    print(f"{len(items)} imagenes con fruto_sano, {sugeridas} sugeridas (puntaje >= {UMBRAL_SUGERIDO})")
    print(f"Abre en el navegador: {html.escape(str(salida))}")


PLANTILLA = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Revisión fruto sano</title>
<style>
:root{--bg:#f6f7f5;--card:#fff;--txt:#1d2420;--sub:#5f6b64;--line:#d9dfdb;--accent:#2f7d4f;--bad:#c0392b;--warn:#b7791f}
@media (prefers-color-scheme:dark){:root{--bg:#141816;--card:#1d2320;--txt:#e7ece9;--sub:#9aa7a0;--line:#2e3833;--accent:#5fbf86;--bad:#ef6f5e;--warn:#e0a84a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:14px/1.4 system-ui,sans-serif}
header{position:sticky;top:0;z-index:2;background:var(--card);border-bottom:1px solid var(--line);padding:12px 16px;display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center}
h1{font-size:16px;margin:0 8px 0 0}.stat{color:var(--sub)}.stat b{color:var(--txt)}
button,label.chk{font:inherit;border:1px solid var(--line);background:var(--bg);color:var(--txt);border-radius:6px;padding:6px 10px;cursor:pointer}
button.prim{background:var(--accent);border-color:var(--accent);color:#fff}
.ayuda{padding:10px 16px;color:var(--sub);max-width:1100px}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;padding:0 16px 32px}
.card{background:var(--card);border:2px solid var(--line);border-radius:8px;overflow:hidden;cursor:pointer;user-select:none}
.card img{display:block;width:100%;aspect-ratio:1;object-fit:contain;background:#000}
.card .info{padding:6px 8px;font-size:12px;color:var(--sub)}
.card .p{font-weight:600;color:var(--txt)}.card .sug{color:var(--warn);font-weight:600}
.card.x{border-color:var(--bad);opacity:.55}.card.x .p::after{content:"  ✕ EXCLUIR";color:var(--bad)}
.card a{color:var(--accent)}
</style></head><body>
<header>
  <h1>Revisión: fruto_sano</h1>
  <span class="stat">Total <b id="nTot"></b> · Sugeridas <b id="nSug"></b> · Marcadas <b id="nMar"></b></span>
  <label class="chk"><input type="checkbox" id="soloSug"> solo sugeridas</label>
  <button id="marcarSug">Marcar sugeridas</button>
  <button id="limpiar">Desmarcar todo</button>
  <button class="prim" id="descargar">Descargar excluir_fruto_sano.txt</button>
</header>
<p class="ayuda">Fíjate solo en los <b style="color:#2f7d4f">recuadros verdes</b> (frutos etiquetados como sanos).
Los <b style="color:#c0392b">recuadros rojos</b> son frutos que ya tienen su etiqueta de enfermedad: no se tocan.
Haz clic en una imagen para marcarla como <b>excluir</b> si algún recuadro verde no es un fruto sano de exportación
(fruta negra/madura, clipart, dibujos, infografías). Al excluir se quitan solo los recuadros verdes de esa imagen; los
rojos se conservan (si no tiene rojos, la imagen sale completa). Las imágenes están ordenadas de más oscura a menos
oscura (el puntaje es solo una ayuda). Las marcas se guardan en este navegador. Al terminar, descarga el archivo y
colócalo en la carpeta <code>revision/</code>.</p>
<main id="g"></main>
<script>
const D=__DATOS__, U=__UMBRAL__, K="excluir_fruto_sano_v1";
let marcadas=new Set();try{marcadas=new Set(JSON.parse(localStorage.getItem(K)||"[]"))}catch(e){}
const g=document.getElementById("g");
function guardar(){try{localStorage.setItem(K,JSON.stringify([...marcadas]))}catch(e){}cuenta()}
function cuenta(){nTot.textContent=D.length;nSug.textContent=D.filter(d=>d.puntaje>=U).length;nMar.textContent=marcadas.size}
function pintar(){
  g.innerHTML="";const solo=soloSug.checked;
  for(const d of D){if(solo&&d.puntaje<U)continue;
    const c=document.createElement("div");c.className="card"+(marcadas.has(d.id)?" x":"");
    c.innerHTML=`<img loading="lazy" src="${d.mini}" alt=""><div class="info"><span class="p">${(d.puntaje*100).toFixed(0)}% oscuro</span>${d.puntaje>=U?' · <span class="sug">sugerida</span>':''}<br>${d.origen} · ${d.frutos} fruto(s) sano(s)${d.otras?`<br><span style="color:var(--bad)">también: ${d.otras}</span>`:''}<br><a href="${d.original}" target="_blank" rel="noopener">ver original</a></div>`;
    c.onclick=e=>{if(e.target.tagName==="A")return;marcadas.has(d.id)?marcadas.delete(d.id):marcadas.add(d.id);c.classList.toggle("x");guardar()};
    g.appendChild(c)}
  cuenta()}
soloSug.onchange=pintar;
marcarSug.onclick=()=>{D.filter(d=>d.puntaje>=U).forEach(d=>marcadas.add(d.id));guardar();pintar()};
limpiar.onclick=()=>{marcadas.clear();guardar();pintar()};
descargar.onclick=()=>{const t=[...marcadas].sort().join("\n")+"\n";const a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob([t],{type:"text/plain"}));a.download="excluir_fruto_sano.txt";a.click()};
pintar();
</script></body></html>
"""

if __name__ == "__main__":
    main()
