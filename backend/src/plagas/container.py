from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .config import Settings
from .modules.catalogo.application.use_cases.obtener_catalogo import ObtenerCatalogo
from .modules.catalogo.infrastructure.catalogo_memoria import CatalogoEnMemoria
from .modules.diagnostico.application.ports import DetectorEnfermedades
from .modules.diagnostico.application.use_cases.diagnosticar_imagen import (
    DiagnosticarImagen,
)
from .modules.diagnostico.application.use_cases.listar_historial import ListarHistorial
from .modules.diagnostico.application.use_cases.obtener_diagnostico import (
    ObtenerDiagnostico,
)
from .modules.diagnostico.domain.value_objects import Organo
from .modules.diagnostico.infrastructure.almacen_local import AlmacenLocal
from .modules.diagnostico.infrastructure.inspector_pillow import (
    InspectorImagenesPillow,
)
from .modules.diagnostico.infrastructure.registro_detectores import RegistroDetectores
from .modules.diagnostico.infrastructure.repositorio_sqlalchemy import (
    RepositorioDiagnosticosSql,
)
from .modules.diagnostico.infrastructure.yolo_detector import DetectorYolo
from .shared.domain.ports import VerificadorTokens
from .shared.infrastructure.db import crear_engine
from .shared.infrastructure.integridad import verificar_sha256
from .shared.infrastructure.oidc import VerificadorFalso, VerificadorJwtOidc
from .shared.infrastructure.reloj import GeneradorUuid4, RelojSistema


@dataclass
class Container:
    settings: Settings
    sesiones: async_sessionmaker[AsyncSession]
    inspector: InspectorImagenesPillow
    detectores: RegistroDetectores
    almacen: AlmacenLocal
    verificador_tokens: VerificadorTokens
    reloj: RelojSistema
    ids: GeneradorUuid4
    catalogo_repo: CatalogoEnMemoria

    @classmethod
    def construir(cls, settings: Settings) -> "Container":
        detectores_dict: dict[Organo, DetectorEnfermedades] = {}

        # 1. Cargar detector de hojas si existe el archivo
        ruta_hojas = settings.modelos_dir / settings.modelo_hojas
        if ruta_hojas.exists():
            verificar_sha256(ruta_hojas, settings.sha256_modelo_hojas)
            detectores_dict[Organo.HOJA] = DetectorYolo(
                ruta_pesos=ruta_hojas,
                imgsz=settings.yolo_imgsz,
                conf_minima=0.10,
            )
        # 2. Cargar detector de frutos si existe el archivo
        ruta_frutos = settings.modelos_dir / settings.modelo_frutos
        if ruta_frutos.exists():
            verificar_sha256(ruta_frutos, settings.sha256_modelo_frutos)
            detectores_dict[Organo.FRUTO] = DetectorYolo(
                ruta_pesos=ruta_frutos,
                imgsz=settings.yolo_imgsz,
                conf_minima=0.10,
            )

        detectores = RegistroDetectores(detectores_dict)
        almacen = AlmacenLocal(settings.almacen_local_dir)

        verificador: VerificadorTokens
        if settings.env == "dev":
            verificador = VerificadorFalso()
        else:
            verificador = VerificadorJwtOidc(
                emisor=settings.oidc_emisor,
                audiencia=settings.oidc_audiencia,
                jwks_url=settings.oidc_jwks_url,
            )

        engine = crear_engine(settings.database_url)
        sesiones = async_sessionmaker(engine, expire_on_commit=False)

        return cls(
            settings=settings,
            sesiones=sesiones,
            inspector=InspectorImagenesPillow(),
            detectores=detectores,
            almacen=almacen,
            verificador_tokens=verificador,
            reloj=RelojSistema(),
            ids=GeneradorUuid4(),
            catalogo_repo=CatalogoEnMemoria(),
        )

    def diagnosticar_imagen(self, sesion: AsyncSession) -> DiagnosticarImagen:
        return DiagnosticarImagen(
            inspector=self.inspector,
            detectores=self.detectores,
            almacen=self.almacen,
            repositorio=RepositorioDiagnosticosSql(sesion),
            reloj=self.reloj,
            ids=self.ids,
            umbral_confianza=self.settings.umbral_confianza,
        )

    def obtener_diagnostico(self, sesion: AsyncSession) -> ObtenerDiagnostico:
        return ObtenerDiagnostico(
            lectura=RepositorioDiagnosticosSql(sesion),
            almacen=self.almacen,
        )

    def listar_historial(self, sesion: AsyncSession) -> ListarHistorial:
        return ListarHistorial(
            lectura=RepositorioDiagnosticosSql(sesion),
            almacen=self.almacen,
        )

    def obtener_catalogo(self) -> ObtenerCatalogo:
        return ObtenerCatalogo(catalogo=self.catalogo_repo)
