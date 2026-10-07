from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from plagas.modules.diagnostico.application.dtos import DiagnosticarImagenCommand
from plagas.modules.diagnostico.application.use_cases.diagnosticar_imagen import DiagnosticarImagen
from plagas.modules.diagnostico.application.use_cases.listar_historial import ListarHistorial
from plagas.modules.diagnostico.application.use_cases.obtener_diagnostico import ObtenerDiagnostico
from plagas.modules.diagnostico.domain.value_objects import Organo
from plagas.shared.api.auth import get_usuario_actual
from plagas.shared.api.seguridad import limiter
from plagas.shared.domain.identidad import Usuario

from .dependencies import (
    get_diagnosticar_imagen,
    get_listar_historial,
    get_obtener_diagnostico,
)
from .schemas import DiagnosticoResponse, DiagnosticosBatchResponse

router = APIRouter(prefix="/diagnosticos", tags=["diagnosticos"])
UsuarioActual = Annotated[Usuario, Depends(get_usuario_actual)]


@router.post("", response_model=DiagnosticoResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def crear_diagnostico(
    request: Request,
    imagen: Annotated[UploadFile, File()],
    usuario: UsuarioActual,
    caso_uso: Annotated[DiagnosticarImagen, Depends(get_diagnosticar_imagen)],
    organo: Annotated[Organo, Form()] = Organo.HOJA,
) -> DiagnosticoResponse:
    comando = DiagnosticarImagenCommand(
        propietario_id=usuario.id,
        organo=organo,
        contenido=await imagen.read(),
        tipo_mime=imagen.content_type or "image/jpeg",
    )
    resultado = await caso_uso.ejecutar(comando)
    return DiagnosticoResponse.model_validate(resultado, from_attributes=True)


@router.post(
    "/batch", response_model=DiagnosticosBatchResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("15/minute")
async def crear_diagnosticos_lote(
    request: Request,
    imagenes: Annotated[list[UploadFile], File()],
    usuario: UsuarioActual,
    caso_uso: Annotated[DiagnosticarImagen, Depends(get_diagnosticar_imagen)],
    organo: Annotated[Organo, Form()] = Organo.HOJA,
) -> DiagnosticosBatchResponse:
    resultados: list[DiagnosticoResponse] = []
    for img in imagenes:
        comando = DiagnosticarImagenCommand(
            propietario_id=usuario.id,
            organo=organo,
            contenido=await img.read(),
            tipo_mime=img.content_type or "image/jpeg",
        )
        dto = await caso_uso.ejecutar(comando)
        resultados.append(DiagnosticoResponse.model_validate(dto, from_attributes=True))

    total = len(resultados)
    total_enfermos = sum(1 for r in resultados if not r.es_sano)
    total_sanos = total - total_enfermos

    return DiagnosticosBatchResponse(
        diagnosticos=resultados,
        total=total,
        total_enfermos=total_enfermos,
        total_sanos=total_sanos,
    )


@router.get("", response_model=list[DiagnosticoResponse])
async def listar_historial(
    usuario: UsuarioActual,
    caso_uso: Annotated[ListarHistorial, Depends(get_listar_historial)],
    limite: int = 50,
    desplazamiento: int = 0,
) -> list[DiagnosticoResponse]:
    dtos = await caso_uso.ejecutar(
        usuario=usuario,
        limite=limite,
        desplazamiento=desplazamiento,
    )
    return [DiagnosticoResponse.model_validate(d, from_attributes=True) for d in dtos]


@router.get("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def obtener_diagnostico(
    diagnostico_id: UUID,
    usuario: UsuarioActual,
    caso_uso: Annotated[ObtenerDiagnostico, Depends(get_obtener_diagnostico)],
) -> DiagnosticoResponse:
    dto = await caso_uso.ejecutar(diagnostico_id, usuario)
    return DiagnosticoResponse.model_validate(dto, from_attributes=True)
