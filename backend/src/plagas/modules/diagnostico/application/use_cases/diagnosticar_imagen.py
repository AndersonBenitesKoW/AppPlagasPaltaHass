from plagas.modules.diagnostico.application.dtos import DiagnosticarImagenCommand, DiagnosticoDTO
from plagas.modules.diagnostico.application.ports import (
    AlmacenImagenes,
    EscrituraDiagnosticos,
    InspectorImagenes,
    ProveedorDetectores,
)
from plagas.modules.diagnostico.domain.entities import Diagnostico
from plagas.modules.diagnostico.domain.value_objects import Imagen
from plagas.shared.domain.ports import GeneradorId, Reloj


class DiagnosticarImagen:
    def __init__(
        self,
        inspector: InspectorImagenes,
        detectores: ProveedorDetectores,
        almacen: AlmacenImagenes,
        repositorio: EscrituraDiagnosticos,
        reloj: Reloj,
        ids: GeneradorId,
        umbral_confianza: float,
    ) -> None:
        self._inspector = inspector
        self._detectores = detectores
        self._almacen = almacen
        self._repositorio = repositorio
        self._reloj = reloj
        self._ids = ids
        self._umbral = umbral_confianza

    async def ejecutar(self, cmd: DiagnosticarImagenCommand) -> DiagnosticoDTO:
        recibida = Imagen(contenido=cmd.contenido, tipo_mime=cmd.tipo_mime)
        detector = self._detectores.para(cmd.organo)
        imagen = await self._inspector.sanear(recibida)
        detecciones = await detector.detectar(imagen)
        imagen_ref = await self._almacen.guardar(imagen)

        diagnostico = Diagnostico.registrar(
            id=self._ids.nuevo(),
            propietario_id=cmd.propietario_id,
            organo=cmd.organo,
            imagen_ref=imagen_ref,
            detecciones=detecciones,
            umbral=self._umbral,
            ahora=self._reloj.ahora(),
        )
        await self._repositorio.guardar(diagnostico)
        imagen_url = await self._almacen.url_publica(imagen_ref)
        return DiagnosticoDTO.desde_entidad(diagnostico, imagen_url)
