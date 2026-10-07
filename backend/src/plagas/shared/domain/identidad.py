from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Usuario:
    id: str
    email: str = ""
    roles: tuple[str, ...] = field(default_factory=lambda: ("agricultor",))

    @property
    def puede_ver_todo(self) -> bool:
        return "admin" in self.roles or "tecnico" in self.roles
