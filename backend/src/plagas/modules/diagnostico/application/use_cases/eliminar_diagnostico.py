from uuid import UUID

from plagas.modules.diagnostico.application.ports import (
    AlmacenImagenes,
    EscrituraDiagnosticos,
    LecturaDiagnosticos,
)
from plagas.modules.diagnostico.domain.errors import DiagnosticoNoEncontrado
from plagas.shared.domain.errors import SinPermiso
from plagas.shared.domain.identidad import Usuario


class EliminarDiagnostico:
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
        diag = await self._lectura.por_id(diagnostico_id)
        if diag is None:
            raise DiagnosticoNoEncontrado(f"Diagnóstico no encontrado: {diagnostico_id}")
        if not diag.visible_para(usuario):
            raise SinPermiso("No tiene autorización para eliminar este diagnóstico")
        await self._escritura.eliminar(diagnostico_id)
        await self._almacen.eliminar(diag.imagen_ref)
