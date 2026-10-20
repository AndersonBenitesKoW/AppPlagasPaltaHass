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
    eliminado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True, nullable=True, default=None
    )


# Columnas agregadas después de la primera versión de la tabla.
_COLUMNAS_NUEVAS = {
    # Los registros previos quedan como "dataset".
    "origen": "VARCHAR(20) NOT NULL DEFAULT 'dataset'",
    # NULL = no está en la papelera.
    "eliminado_en": "TIMESTAMP NULL",
}


def migrar_columnas(conn: Connection) -> None:
    """Agrega a bases existentes las columnas nuevas, que `create_all` no crea en tablas viejas."""
    columnas = {c["name"] for c in inspect(conn).get_columns(DiagnosticoORM.__tablename__)}
    for nombre, definicion in _COLUMNAS_NUEVAS.items():
        if nombre not in columnas:
            conn.execute(text(f"ALTER TABLE diagnosticos ADD COLUMN {nombre} {definicion}"))
