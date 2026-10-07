from typing import Protocol

from plagas.modules.catalogo.domain.entities import Enfermedad


class RepositorioCatalogo(Protocol):
    async def listar(self, organo: str | None = None) -> list[Enfermedad]: ...
    async def por_codigo(self, codigo: str) -> Enfermedad | None: ...
