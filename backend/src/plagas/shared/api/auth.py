from typing import Annotated, Any

from fastapi import Depends, Header, Request

from plagas.shared.domain.identidad import Usuario

from .dependencias import get_container


async def get_usuario_actual(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    container: Any = Depends(get_container),
) -> Usuario:
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        usuario: Usuario = container.verificador_tokens.verificar(token)
        return usuario

    # En entorno dev permitimos usuario de trabajo por defecto para facilitar pruebas y uso ágil
    if getattr(container.settings, "env", "dev") == "dev":
        return Usuario(
            id="agricultor1", email="agricultor@palta.app", roles=("agricultor", "admin")
        )

    from plagas.shared.domain.errors import NoAutenticado

    raise NoAutenticado("Cabecera Authorization requerida")
