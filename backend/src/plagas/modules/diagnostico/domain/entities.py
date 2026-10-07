from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from plagas.shared.domain.identidad import Usuario

from .value_objects import Deteccion, Organo


@dataclass(slots=True)
class Diagnostico:
    id: UUID
    propietario_id: str
    organo: Organo
    imagen_ref: str
    creado_en: datetime
    detecciones: tuple[Deteccion, ...] = field(default_factory=tuple)

    @classmethod
    def registrar(
        cls,
        *,
        id: UUID,
        propietario_id: str,
        organo: Organo,
        imagen_ref: str,
        detecciones: list[Deteccion],
        umbral: float,
        ahora: datetime,
    ) -> "Diagnostico":
        filtradas = tuple(d for d in detecciones if d.confianza.valor >= umbral)
        return cls(
            id=id,
            propietario_id=propietario_id,
            organo=organo,
            imagen_ref=imagen_ref,
            creado_en=ahora,
            detecciones=filtradas,
        )

    def visible_para(self, usuario: Usuario) -> bool:
        return self.propietario_id == usuario.id or usuario.puede_ver_todo

    @property
    def enfermedades(self) -> list[str]:
        return sorted({d.clase for d in self.detecciones if not d.es_sana})

    @property
    def es_sano(self) -> bool:
        return len(self.enfermedades) == 0
