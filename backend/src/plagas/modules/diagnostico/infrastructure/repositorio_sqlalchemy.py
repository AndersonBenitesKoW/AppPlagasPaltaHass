from uuid import UUID

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from plagas.modules.diagnostico.domain.entities import Diagnostico
from plagas.modules.diagnostico.domain.value_objects import (
    CajaDelimitadora,
    Confianza,
    Deteccion,
    Organo,
)

from .orm import DiagnosticoORM


class RepositorioDiagnosticosSql:
    """Implementa EscrituraDiagnosticos y LecturaDiagnosticos con SQLAlchemy async."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def guardar(self, diagnostico: Diagnostico) -> None:
        raw_detecciones = [
            {
                "clase": d.clase,
                "confianza": d.confianza.valor,
                "caja": {
                    "x1": d.caja.x1,
                    "y1": d.caja.y1,
                    "x2": d.caja.x2,
                    "y2": d.caja.y2,
                },
            }
            for d in diagnostico.detecciones
        ]

        obj = DiagnosticoORM(
            id=str(diagnostico.id),
            propietario_id=diagnostico.propietario_id,
            organo=diagnostico.organo.value,
            imagen_ref=diagnostico.imagen_ref,
            es_sano=diagnostico.es_sano,
            enfermedades=diagnostico.enfermedades,
            detecciones=raw_detecciones,
            creado_en=diagnostico.creado_en,
        )
        self._sesion.add(obj)
        await self._sesion.flush()

    async def eliminar(self, id: UUID) -> bool:
        stmt = delete(DiagnosticoORM).where(DiagnosticoORM.id == str(id))
        result = await self._sesion.execute(stmt)
        await self._sesion.flush()
        rowcount = int(getattr(result, "rowcount", 0) or 0)
        return rowcount > 0

    async def por_id(self, id: UUID) -> Diagnostico | None:
        stmt = select(DiagnosticoORM).where(DiagnosticoORM.id == str(id))
        result = await self._sesion.execute(stmt)
        fila = result.scalar_one_or_none()
        if fila is None:
            return None
        return self._a_entidad(fila)

    async def recientes(
        self,
        propietario_id: str | None = None,
        limite: int = 50,
        desplazamiento: int = 0,
    ) -> list[Diagnostico]:
        stmt = select(DiagnosticoORM).order_by(desc(DiagnosticoORM.creado_en))
        if propietario_id is not None:
            stmt = stmt.where(DiagnosticoORM.propietario_id == propietario_id)
        stmt = stmt.limit(limite).offset(desplazamiento)
        result = await self._sesion.execute(stmt)
        filas = result.scalars().all()
        return [self._a_entidad(f) for f in filas]

    def _a_entidad(self, orm: DiagnosticoORM) -> Diagnostico:
        detecciones: list[Deteccion] = []
        for d in orm.detecciones or []:
            c = d.get("caja", {})
            detecciones.append(
                Deteccion(
                    clase=d.get("clase", ""),
                    confianza=Confianza(float(d.get("confianza", 0.0))),
                    caja=CajaDelimitadora(
                        x1=float(c.get("x1", 0.0)),
                        y1=float(c.get("y1", 0.0)),
                        x2=float(c.get("x2", 0.0)),
                        y2=float(c.get("y2", 0.0)),
                    ),
                )
            )
        return Diagnostico(
            id=UUID(orm.id),
            propietario_id=orm.propietario_id,
            organo=Organo(orm.organo),
            imagen_ref=orm.imagen_ref,
            creado_en=orm.creado_en,
            detecciones=tuple(detecciones),
        )
