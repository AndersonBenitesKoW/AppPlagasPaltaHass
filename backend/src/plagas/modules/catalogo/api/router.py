from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from plagas.shared.api.dependencias import get_container

from .schemas import EnfermedadResponse

router = APIRouter(prefix="/catalogo", tags=["catalogo"])


def get_obtener_catalogo(container: Any = Depends(get_container)) -> Any:
    return container.obtener_catalogo()


@router.get("", response_model=list[EnfermedadResponse])
async def listar_catalogo(
    organo: str | None = None,
    caso_uso: Any = Depends(get_obtener_catalogo),
) -> list[EnfermedadResponse]:
    enfermedades = await caso_uso.ejecutar(organo)
    return [EnfermedadResponse.model_validate(e, from_attributes=True) for e in enfermedades]


@router.get("/{codigo}", response_model=EnfermedadResponse)
async def obtener_enfermedad(
    codigo: str,
    caso_uso: Any = Depends(get_obtener_catalogo),
) -> EnfermedadResponse:
    item = await caso_uso.por_codigo(codigo)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enfermedad con código '{codigo}' no encontrada en el catálogo",
        )
    return EnfermedadResponse.model_validate(item, from_attributes=True)
