from plagas.modules.catalogo.application.ports import RepositorioCatalogo
from plagas.modules.catalogo.domain.entities import Enfermedad


class ObtenerCatalogo:
    def __init__(self, catalogo: RepositorioCatalogo) -> None:
        self._catalogo = catalogo

    async def ejecutar(self, organo: str | None = None) -> list[Enfermedad]:
        return await self._catalogo.listar(organo)

    async def por_codigo(self, codigo: str) -> Enfermedad | None:
        return await self._catalogo.por_codigo(codigo)
