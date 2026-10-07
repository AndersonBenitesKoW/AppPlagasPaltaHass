from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from plagas.shared.infrastructure.db import Base


class DiagnosticoORM(Base):
    __tablename__ = "diagnosticos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    propietario_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    organo: Mapped[str] = mapped_column(String(20), nullable=False)
    imagen_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    es_sano: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enfermedades: Mapped[list[str]] = mapped_column(
        JSON().with_variant(SQLITE_JSON, "sqlite"), default=list
    )
    detecciones: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(SQLITE_JSON, "sqlite"), default=list
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
