from pydantic import BaseModel, ConfigDict


class EnfermedadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str
    organo: str
    severidad: str
    descripcion: str
    sintomas: list[str]
    recomendaciones: list[str]
