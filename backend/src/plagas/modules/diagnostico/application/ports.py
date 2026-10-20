from datetime import datetime
from typing import Protocol
from uuid import UUID

from plagas.modules.diagnostico.domain.entities import Diagnostico
from plagas.modules.diagnostico.domain.value_objects import Deteccion, Imagen, Organo


class InspectorImagenes(Protocol):
    async def sanear(self, imagen: Imagen) -> Imagen: ...


class DetectorEnfermedades(Protocol):
    async def detectar(self, imagen: Imagen) -> list[Deteccion]: ...


class ProveedorDetectores(Protocol):
    def para(self, organo: Organo) -> DetectorEnfermedades: ...


class AlmacenImagenes(Protocol):
    async def guardar(self, imagen: Imagen) -> str: ...
    async def url_publica(self, referencia: str) -> str: ...
    async def eliminar(self, referencia: str) -> None: ...


class EscrituraDiagnosticos(Protocol):
    async def guardar(self, diagnostico: Diagnostico) -> None: ...
    async def eliminar(self, id: UUID) -> bool: ...
    async def marcar_eliminado(self, id: UUID, cuando: datetime | None) -> None: ...


class LecturaDiagnosticos(Protocol):
    async def por_id(self, id: UUID) -> Diagnostico | None: ...
    async def recientes(
        self,
        propietario_id: str | None = None,
        limite: int = 50,
        desplazamiento: int = 0,
        en_papelera: bool = False,
    ) -> list[Diagnostico]: ...
