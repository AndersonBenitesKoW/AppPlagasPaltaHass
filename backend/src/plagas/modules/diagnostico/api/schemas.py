from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from plagas.modules.diagnostico.domain.value_objects import Organo


class CajaSchema(BaseModel):
    x1: float = Field(ge=0, le=1)
    y1: float = Field(ge=0, le=1)
    x2: float = Field(ge=0, le=1)
    y2: float = Field(ge=0, le=1)


class DeteccionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clase: str
    confianza: float = Field(ge=0, le=1)
    caja: CajaSchema


class DiagnosticoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organo: Organo
    propietario_id: str
    es_sano: bool
    enfermedades: list[str]
    detecciones: list[DeteccionSchema]
    imagen_url: str
    creado_en: datetime


class DiagnosticosBatchResponse(BaseModel):
    diagnosticos: list[DiagnosticoResponse]
    total: int
    total_enfermos: int
    total_sanos: int
