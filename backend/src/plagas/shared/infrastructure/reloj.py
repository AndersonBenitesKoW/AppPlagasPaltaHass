from datetime import UTC, datetime
from uuid import UUID, uuid4


class RelojSistema:
    def ahora(self) -> datetime:
        return datetime.now(UTC)


class GeneradorUuid4:
    def nuevo(self) -> UUID:
        return uuid4()
