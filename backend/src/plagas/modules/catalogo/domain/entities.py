from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Enfermedad:
    codigo: str
    nombre: str
    organo: str
    severidad: str
    descripcion: str
    sintomas: tuple[str, ...] = field(default_factory=tuple)
    recomendaciones: tuple[str, ...] = field(default_factory=tuple)
