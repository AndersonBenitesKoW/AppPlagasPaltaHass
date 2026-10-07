from plagas.modules.diagnostico.application.dtos import DiagnosticoDTO
from plagas.modules.diagnostico.application.ports import AlmacenImagenes, LecturaDiagnosticos
from plagas.shared.domain.identidad import Usuario


class ListarHistorial:
    def __init__(self, lectura: LecturaDiagnosticos, almacen: AlmacenImagenes) -> None:
        self._lectura = lectura
        self._almacen = almacen

    async def ejecutar(
        self,
        usuario: Usuario,
        limite: int = 50,
        desplazamiento: int = 0,
    ) -> list[DiagnosticoDTO]:
        propietario = None if usuario.puede_ver_todo else usuario.id
        entidades = await self._lectura.recientes(
            propietario_id=propietario,
            limite=limite,
            desplazamiento=desplazamiento,
        )
        resultados: list[DiagnosticoDTO] = []
        for ent in entidades:
            url = await self._almacen.url_publica(ent.imagen_ref)
            resultados.append(DiagnosticoDTO.desde_entidad(ent, url))
        return resultados
