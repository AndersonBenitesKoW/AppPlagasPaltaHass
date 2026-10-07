from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from plagas.modules.diagnostico.domain.entities import Diagnostico
from plagas.modules.diagnostico.domain.value_objects import Organo


@dataclass(frozen=True, slots=True)
class DiagnosticarImagenCommand:
    propietario_id: str
    organo: Organo
    contenido: bytes
    tipo_mime: str


@dataclass(frozen=True, slots=True)
class CajaDTO:
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True, slots=True)
class DeteccionDTO:
    clase: str
    confianza: float
    caja: CajaDTO


@dataclass(frozen=True, slots=True)
class DiagnosticoDTO:
    id: UUID
    organo: Organo
    propietario_id: str
    es_sano: bool
    enfermedades: list[str]
    detecciones: list[DeteccionDTO]
    imagen_url: str
    creado_en: datetime

    @classmethod
    def desde_entidad(cls, entidad: Diagnostico, imagen_url: str) -> "DiagnosticoDTO":
        return cls(
            id=entidad.id,
            organo=entidad.organo,
            propietario_id=entidad.propietario_id,
            es_sano=entidad.es_sano,
            enfermedades=entidad.enfermedades,
            detecciones=[
                DeteccionDTO(
                    clase=d.clase,
                    confianza=d.confianza.valor,
                    caja=CajaDTO(
                        x1=d.caja.x1,
                        y1=d.caja.y1,
                        x2=d.caja.x2,
                        y2=d.caja.y2,
                    ),
                )
                for d in entidad.detecciones
            ],
            imagen_url=imagen_url,
            creado_en=entidad.creado_en,
        )
