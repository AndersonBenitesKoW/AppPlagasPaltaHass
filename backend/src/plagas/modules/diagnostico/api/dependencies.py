from collections.abc import AsyncIterator
from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from plagas.shared.api.dependencias import get_container


async def get_sesion(container: Any = Depends(get_container)) -> AsyncIterator[AsyncSession]:
    async with container.sesiones() as sesion, sesion.begin():
        yield sesion


def get_diagnosticar_imagen(
    container: Any = Depends(get_container),
    sesion: AsyncSession = Depends(get_sesion),
) -> Any:
    return container.diagnosticar_imagen(sesion)


def get_obtener_diagnostico(
    container: Any = Depends(get_container),
    sesion: AsyncSession = Depends(get_sesion),
) -> Any:
    return container.obtener_diagnostico(sesion)


def get_listar_historial(
    container: Any = Depends(get_container),
    sesion: AsyncSession = Depends(get_sesion),
) -> Any:
    return container.listar_historial(sesion)
