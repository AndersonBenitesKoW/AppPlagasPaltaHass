from datetime import datetime
from typing import Protocol
from uuid import UUID

from .identidad import Usuario


class Reloj(Protocol):
    def ahora(self) -> datetime: ...


class GeneradorId(Protocol):
    def nuevo(self) -> UUID: ...


class VerificadorTokens(Protocol):
    def verificar(self, token: str) -> Usuario: ...
