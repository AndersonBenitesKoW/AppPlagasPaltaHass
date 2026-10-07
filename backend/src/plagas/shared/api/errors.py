from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from plagas.shared.domain.errors import ErrorDominio, LimiteExcedido, NoAutenticado, SinPermiso

log = structlog.get_logger()

STATUS_POR_ERROR: dict[type[ErrorDominio], int] = {
    NoAutenticado: status.HTTP_401_UNAUTHORIZED,
    SinPermiso: status.HTTP_403_FORBIDDEN,
    LimiteExcedido: status.HTTP_429_TOO_MANY_REQUESTS,
}


def _problema(
    status_code: int,
    codigo: str,
    detalle: str,
    request: Request,
    **extra: Any,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status_code,
        media_type="application/problem+json",
        content={
            "type": f"https://plagas-palta.app/errores/{codigo}",
            "title": codigo,
            "status": status_code,
            "detail": detalle,
            "instance": request.url.path,
            "request_id": request_id,
            **extra,
        },
    )


def registrar_manejadores_error(app: FastAPI) -> None:
    @app.exception_handler(ErrorDominio)
    async def _dominio(request: Request, exc: ErrorDominio) -> JSONResponse:
        status_code = next(
            (s for t, s in STATUS_POR_ERROR.items() if isinstance(exc, t)),
            status.HTTP_400_BAD_REQUEST,
        )
        log.info("error_dominio", codigo=exc.codigo, status=status_code, mensaje=exc.mensaje)
        respuesta = _problema(status_code, exc.codigo, exc.mensaje, request)
        if status_code == status.HTTP_401_UNAUTHORIZED:
            respuesta.headers["WWW-Authenticate"] = "Bearer"
        return respuesta

    @app.exception_handler(RequestValidationError)
    async def _validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _problema(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validacion",
            "Datos de entrada inválidos",
            request,
            errors=exc.errors(),
        )

    @app.exception_handler(Exception)
    async def _inesperado(request: Request, exc: Exception) -> JSONResponse:
        log.exception("error_no_controlado", error=str(exc))
        return _problema(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error_interno",
            "Ocurrió un error inesperado",
            request,
        )
