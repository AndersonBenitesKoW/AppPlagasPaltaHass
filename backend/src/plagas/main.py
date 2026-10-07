from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import Settings
from .container import Container
from .modules.catalogo.api.router import router as catalogo_router
from .modules.diagnostico.api.router import router as diagnostico_router
from .shared.api.errors import registrar_manejadores_error
from .shared.api.health import router as health_router
from .shared.api.middlewares import RequestContextMiddleware
from .shared.infrastructure.db import Base
from .shared.infrastructure.logging import configurar_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Crear tablas en BD automáticamente al inicio
    engine = app.state.container.sesiones.kw["bind"]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = Settings()

    configurar_logging(nivel=settings.log_level, salida_json=(settings.env != "dev"))
    container = Container.construir(settings)

    app = FastAPI(
        title="App Plagas Palta Hass API",
        version="0.1.0",
        description="API para diagnóstico de plagas y enfermedades en palta Hass con modelos YOLO",
        lifespan=lifespan,
    )

    app.state.container = container
    app.state.settings = settings

    # Middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.hosts_permitidos)

    # Manejadores de error RFC 9457
    registrar_manejadores_error(app)

    # Routers
    app.include_router(health_router)
    app.include_router(diagnostico_router, prefix="/api/v1")
    app.include_router(catalogo_router, prefix="/api/v1")

    # Servir imágenes almacenadas
    @app.get("/api/v1/imagenes/{nombre_archivo}", tags=["imagenes"])
    async def obtener_imagen(nombre_archivo: str) -> FileResponse:
        ruta = Path(settings.almacen_local_dir) / nombre_archivo
        if not ruta.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Imagen no encontrada",
            )
        media_type = "image/jpeg" if ruta.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
        return FileResponse(ruta, media_type=media_type)

    return app
