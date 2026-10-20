from uuid import UUID

from plagas.modules.diagnostico.application.dtos import DiagnosticoDTO
from plagas.modules.diagnostico.application.ports import (
    AlmacenImagenes,
    EscrituraDiagnosticos,
    LecturaDiagnosticos,
)
from plagas.modules.diagnostico.domain.entities import Diagnostico
from plagas.modules.diagnostico.domain.errors import DiagnosticoNoEncontrado
from plagas.shared.domain.errors import SinPermiso
from plagas.shared.domain.identidad import Usuario
from plagas.shared.domain.ports import Reloj


async def _cargar_visible(
    lectura: LecturaDiagnosticos, diagnostico_id: UUID, usuario: Usuario
) -> Diagnostico:
    diag = await lectura.por_id(diagnostico_id)
    if diag is None:
        raise DiagnosticoNoEncontrado(f"Diagnóstico no encontrado: {diagnostico_id}")
    if not diag.visible_para(usuario):
        raise SinPermiso("No tiene autorización para modificar este diagnóstico")
    return diag


class MoverAPapelera:
    """Borrado lógico: el diagnóstico deja de verse en el historial pero puede restaurarse."""

    def __init__(
        self, lectura: LecturaDiagnosticos, escritura: EscrituraDiagnosticos, reloj: Reloj
    ) -> None:
        self._lectura = lectura
        self._escritura = escritura
        self._reloj = reloj

    async def ejecutar(self, diagnostico_id: UUID, usuario: Usuario) -> None:
        await _cargar_visible(self._lectura, diagnostico_id, usuario)
        await self._escritura.marcar_eliminado(diagnostico_id, self._reloj.ahora())


class RestaurarDiagnostico:
    def __init__(
        self,
        lectura: LecturaDiagnosticos,
        escritura: EscrituraDiagnosticos,
        almacen: AlmacenImagenes,
    ) -> None:
        self._lectura = lectura
        self._escritura = escritura
        self._almacen = almacen

    async def ejecutar(self, diagnostico_id: UUID, usuario: Usuario) -> DiagnosticoDTO:
        diag = await _cargar_visible(self._lectura, diagnostico_id, usuario)
        await self._escritura.marcar_eliminado(diagnostico_id, None)
        diag.eliminado_en = None
        url = await self._almacen.url_publica(diag.imagen_ref)
        return DiagnosticoDTO.desde_entidad(diag, url)


class EliminarDefinitivo:
    """Borra el registro de la base de datos y su imagen del almacén. No se puede deshacer."""

    def __init__(
        self,
        lectura: LecturaDiagnosticos,
        escritura: EscrituraDiagnosticos,
        almacen: AlmacenImagenes,
    ) -> None:
        self._lectura = lectura
        self._escritura = escritura
        self._almacen = almacen

    async def ejecutar(self, diagnostico_id: UUID, usuario: Usuario) -> None:
        diag = await _cargar_visible(self._lectura, diagnostico_id, usuario)
        await self._escritura.eliminar(diagnostico_id)
        await self._almacen.eliminar(diag.imagen_ref)


class VaciarPapelera:
    def __init__(
        self,
        lectura: LecturaDiagnosticos,
        escritura: EscrituraDiagnosticos,
        almacen: AlmacenImagenes,
    ) -> None:
        self._lectura = lectura
        self._escritura = escritura
        self._almacen = almacen

    async def ejecutar(self, usuario: Usuario) -> int:
        propietario = None if usuario.puede_ver_todo else usuario.id
        en_papelera = await self._lectura.recientes(
            propietario_id=propietario, limite=10_000, en_papelera=True
        )
        for diag in en_papelera:
            await self._escritura.eliminar(diag.id)
            await self._almacen.eliminar(diag.imagen_ref)
        return len(en_papelera)
