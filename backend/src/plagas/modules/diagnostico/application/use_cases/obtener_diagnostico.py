from uuid import UUID

from plagas.modules.diagnostico.application.dtos import DiagnosticoDTO
from plagas.modules.diagnostico.application.ports import AlmacenImagenes, LecturaDiagnosticos
from plagas.modules.diagnostico.domain.errors import DiagnosticoNoEncontrado
from plagas.shared.domain.errors import SinPermiso
from plagas.shared.domain.identidad import Usuario


class ObtenerDiagnostico:
    def __init__(self, lectura: LecturaDiagnosticos, almacen: AlmacenImagenes) -> None:
        self._lectura = lectura
        self._almacen = almacen

    async def ejecutar(self, diagnostico_id: UUID, usuario: Usuario) -> DiagnosticoDTO:
        diag = await self._lectura.por_id(diagnostico_id)
        if diag is None:
            raise DiagnosticoNoEncontrado(f"Diagnóstico no encontrado: {diagnostico_id}")
        if not diag.visible_para(usuario):
            raise SinPermiso("No tiene autorización para ver este diagnóstico")
        url = await self._almacen.url_publica(diag.imagen_ref)
        return DiagnosticoDTO.desde_entidad(diag, url)
