from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Connection, DateTime, String, inspect, text
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
    origen: Mapped[str] = mapped_column(
        String(20), nullable=False, default="dataset", server_default="dataset", index=True
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)


def migrar_columna_origen(conn: Connection) -> None:
    """Agrega la columna `origen` a bases creadas antes de que existiera.

    `create_all` no altera tablas existentes; los registros previos quedan como "dataset".
    """
    columnas = {c["name"] for c in inspect(conn).get_columns(DiagnosticoORM.__tablename__)}
    if "origen" not in columnas:
        conn.execute(
            text(
                "ALTER TABLE diagnosticos "
                "ADD COLUMN origen VARCHAR(20) NOT NULL DEFAULT 'dataset'"
            )
        )
