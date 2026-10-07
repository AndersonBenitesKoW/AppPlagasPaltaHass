import uuid
from pathlib import Path

import anyio

from plagas.modules.diagnostico.domain.value_objects import Imagen


class AlmacenLocal:
    """Implementa AlmacenImagenes guardando en disco local."""

    def __init__(self, ruta_directorio: Path, prefijo_url: str = "/api/v1/imagenes") -> None:
        self._dir = Path(ruta_directorio)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._prefijo_url = prefijo_url.rstrip("/")

    async def guardar(self, imagen: Imagen) -> str:
        extension = "jpg" if imagen.tipo_mime == "image/jpeg" else "png"
        nombre = f"{uuid.uuid4().hex}.{extension}"
        destino = self._dir / nombre
        await anyio.to_thread.run_sync(destino.write_bytes, imagen.contenido)
        return nombre

    async def url_publica(self, referencia: str) -> str:
        return f"{self._prefijo_url}/{referencia}"

    def ruta_fisica(self, referencia: str) -> Path:
        return self._dir / referencia
