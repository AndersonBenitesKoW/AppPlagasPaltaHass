from dataclasses import dataclass
from enum import StrEnum

from .errors import ConfianzaInvalida, ImagenInvalida

MIME_PERMITIDOS = frozenset({"image/jpeg", "image/png", "image/webp"})
TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024


class Organo(StrEnum):
    HOJA = "hoja"
    FRUTO = "fruto"


@dataclass(frozen=True, slots=True)
class Confianza:
    valor: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.valor <= 1.0:
            raise ConfianzaInvalida(self.valor)


@dataclass(frozen=True, slots=True)
class CajaDelimitadora:
    """Coordenadas normalizadas (0..1) para ser independientes de la resolución."""

    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True, slots=True)
class Deteccion:
    clase: str
    confianza: Confianza
    caja: CajaDelimitadora

    @property
    def es_sana(self) -> bool:
        return self.clase.endswith(("_sana", "_sano"))


@dataclass(frozen=True, slots=True)
class Imagen:
    contenido: bytes
    tipo_mime: str

    def __post_init__(self) -> None:
        if self.tipo_mime not in MIME_PERMITIDOS:
            raise ImagenInvalida(f"Formato no soportado: {self.tipo_mime}")
        if not self.contenido:
            raise ImagenInvalida("La imagen está vacía")
        if len(self.contenido) > TAMANO_MAXIMO_BYTES:
            raise ImagenInvalida("La imagen supera los 10 MB permitidos")
