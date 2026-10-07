import io

import anyio
from PIL import Image as PILImage

from plagas.modules.diagnostico.domain.errors import ImagenInvalida
from plagas.modules.diagnostico.domain.value_objects import Imagen


class InspectorImagenesPillow:
    """Sanea imágenes: valida bytes mágicos, limita tamaño y remueve EXIF/GPS."""

    MAX_PIXELS = 25_000_000  # máx 25 MP para evitar bombas

    async def sanear(self, imagen: Imagen) -> Imagen:
        return await anyio.to_thread.run_sync(self._sanear_sync, imagen)

    def _sanear_sync(self, imagen: Imagen) -> Imagen:
        try:
            buffer = io.BytesIO(imagen.contenido)
            with PILImage.open(buffer) as pil:
                formato = pil.format
                if formato not in {"JPEG", "PNG", "WEBP"}:
                    raise ImagenInvalida(f"Formato no admitido por decodificador: {formato}")

                ancho, alto = pil.size
                if ancho * alto > self.MAX_PIXELS:
                    raise ImagenInvalida("La resolución de la imagen es excesiva")

                # Re-codificar en RGB puro removiendo metadatos EXIF / geolocalización
                limpia = PILImage.new("RGB", pil.size)
                if pil.mode in ("RGBA", "LA") or (pil.mode == "P" and "transparency" in pil.info):
                    limpia.paste(pil.convert("RGBA"), mask=pil.convert("RGBA").split()[3])
                else:
                    limpia.paste(pil.convert("RGB"))

                out = io.BytesIO()
                limpia.save(out, format="JPEG", quality=90, optimize=True)
                return Imagen(contenido=out.getvalue(), tipo_mime="image/jpeg")
        except ImagenInvalida:
            raise
        except Exception as e:
            raise ImagenInvalida(f"Archivo de imagen corrupto o ilegible: {e}") from e
