# Arquitectura: App de diagnóstico de plagas y enfermedades en palta Hass

Documento de diseño del sistema web que usa los modelos YOLO11 entrenados (ver `ESTRATEGIA_DATASET.md`) para diagnosticar enfermedades en **hojas** y **frutos** de palta Hass a partir de una foto.

- **Backend:** Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2 (async) + Ultralytics YOLO11.
- **Frontend:** React 19 + Vite + TypeScript + TanStack Query + Zod.
- **Paradigma:** Clean Architecture / Hexagonal (Ports & Adapters) en backend; Feature-driven (Screaming Architecture) en frontend.
- **Despliegue:** frontend y backend en contenedores independientes; se comunican solo por HTTP con un contrato OpenAPI.

---

## 0. Dominio del problema (lenguaje ubicuo)

| Término | Significado |
|---|---|
| **Órgano** | Parte de la planta fotografiada: `hoja` o `fruto`. Decide qué modelo se usa. |
| **Detección** | Una caja con clase y confianza devuelta por el modelo. |
| **Diagnóstico** | Resultado de analizar una imagen: órgano, detecciones, veredicto (sano / enfermo) y fecha. |
| **Enfermedad** | Entrada del catálogo: código de clase (`antracnosis_fruto`), nombre, descripción, recomendaciones de manejo. |
| **Detector** | Componente que, dado un órgano, ejecuta el modelo correspondiente. |

Clases actuales (salen de `DatasetHojas/data.yaml` y `DatasetFrutos/data.yaml`):

- **Hoja:** `hoja_sana`, `antracnosis_hoja`, `plaga`, `deficiencia_nutricional`
- **Fruto:** `fruto_sano`, `antracnosis_fruto`, `cercospora`, `rona`, `pudricion_peduncular`, `sunblotch`

Regla de negocio central: **un diagnóstico es "sano" si no hay ninguna detección de enfermedad por encima del umbral de confianza**. Las clases `*_sana`/`*_sano` no cuentan como enfermedad.

---

## A. Árbol de directorios (monorepo)

Se elige **monorepo** porque el contrato API, los pesos del modelo y el código de entrenamiento evolucionan juntos. Cada app tiene su propio `Dockerfile` y se despliega por separado.

```
AppWebPlagasPaltaHass/
├── backend/
│   ├── pyproject.toml              # deps (uv), ruff, mypy, pytest, import-linter
│   ├── uv.lock
│   ├── Dockerfile
│   ├── .env.example
│   ├── models/                     # pesos en producción (no versionados en git; ver §D.4)
│   │   ├── hojas.pt
│   │   ├── frutos.pt
│   │   └── manifest.json           # versión, fecha, métricas mAP de cada peso
│   ├── alembic/                    # migraciones de BD
│   ├── src/plagas/
│   │   ├── main.py                 # create_app(): solo arma la app, no tiene lógica
│   │   ├── config.py               # Settings (pydantic-settings)
│   │   ├── container.py            # Composition Root: único lugar que conoce las clases concretas
│   │   │
│   │   ├── shared/                 # Kernel compartido (sin dependencias de módulos)
│   │   │   ├── domain/
│   │   │   │   ├── errors.py       # ErrorDominio base, NoAutenticado, SinPermiso
│   │   │   │   ├── identidad.py    # Usuario (id, roles)
│   │   │   │   └── ports.py        # Reloj, GeneradorId, VerificadorTokens
│   │   │   ├── infrastructure/
│   │   │   │   ├── db.py           # engine, session factory, Base
│   │   │   │   ├── logging.py      # structlog JSON + redacción de secretos
│   │   │   │   ├── oidc.py         # VerificadorJwtOidc (JWKS)
│   │   │   │   ├── integridad.py   # verificación SHA-256 de pesos del modelo
│   │   │   │   └── reloj.py        # RelojSistema
│   │   │   └── api/
│   │   │       ├── errors.py       # ErrorDominio -> application/problem+json
│   │   │       ├── middlewares.py  # request-id, logging de acceso
│   │   │       ├── seguridad.py    # cabeceras, límite de cuerpo, rate limiting
│   │   │       ├── auth.py         # get_usuario_actual (Bearer JWT)
│   │   │       ├── dependencias.py # get_container (compartido por todos los módulos)
│   │   │       └── health.py       # /health/live, /health/ready
│   │   │
│   │   └── modules/                # Un módulo = un bounded context vertical
│   │       ├── diagnostico/
│   │       │   ├── domain/
│   │       │   │   ├── entities.py         # Diagnostico
│   │       │   │   ├── value_objects.py    # Organo, Confianza, CajaDelimitadora, Deteccion, Imagen
│   │       │   │   └── errors.py           # ImagenInvalida, OrganoNoSoportado, DiagnosticoNoEncontrado
│   │       │   ├── application/
│   │       │   │   ├── ports.py            # DetectorEnfermedades, ProveedorDetectores, AlmacenImagenes, repos
│   │       │   │   ├── dtos.py             # Commands / Queries / DTOs de salida
│   │       │   │   └── use_cases/
│   │       │   │       ├── diagnosticar_imagen.py
│   │       │   │       ├── obtener_diagnostico.py
│   │       │   │       └── listar_historial.py
│   │       │   ├── infrastructure/
│   │       │   │   ├── yolo_detector.py         # adapter Ultralytics
│   │       │   │   ├── registro_detectores.py   # Organo -> DetectorYolo
│   │       │   │   ├── inspector_pillow.py      # magic bytes, bombas, quita EXIF/GPS
│   │       │   │   ├── almacen_local.py         # imágenes en disco/volumen
│   │       │   │   ├── almacen_s3.py            # imágenes en S3/MinIO
│   │       │   │   ├── orm.py                   # tablas SQLAlchemy
│   │       │   │   └── repositorio_sqlalchemy.py
│   │       │   └── api/
│   │       │       ├── router.py           # endpoints HTTP (solo transporte)
│   │       │       ├── schemas.py          # Pydantic request/response
│   │       │       └── dependencies.py     # Depends() que piden casos de uso al container
│   │       │
│   │       └── catalogo/                   # Enfermedades y recomendaciones de manejo
│   │           ├── domain/ application/ infrastructure/ api/   # misma forma
│   │
│   └── tests/                      # ver §F
│       ├── conftest.py             # fixtures globales
│       ├── fakes.py                # dobles de prueba de todos los puertos
│       ├── factories.py            # constructores de datos de prueba
│       ├── fixtures/imagenes/      # golden set para regresión del modelo
│       ├── unit/                   # dominio + casos de uso con fakes (sin BD, sin YOLO)
│       ├── contract/               # misma suite contra fake y adapter real (LSP)
│       ├── integration/            # repos con Postgres (testcontainers), inspector Pillow
│       ├── modelo/                 # regresión de YOLO con pesos reales
│       └── api/                    # httpx.AsyncClient contra la app (auth, errores, límites)
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── eslint.config.js            # incluye eslint-plugin-boundaries (§B)
│   ├── Dockerfile
│   ├── vitest.config.ts
│   ├── nginx/
│   │   ├── default.conf.template   # server, caché, SPA
│   │   ├── seguridad.inc.template  # cabeceras de seguridad + CSP con las URLs del ambiente
│   │   └── 40-runtime-config.sh    # genera config.js desde variables de entorno
│   ├── public/
│   │   └── config.js.template
│   ├── .env.example
│   └── src/
│       ├── main.tsx
│       ├── app/                    # Composición de la aplicación
│       │   ├── App.tsx
│       │   ├── providers.tsx       # QueryClient, ErrorBoundary, Theme
│       │   └── router.tsx          # rutas, lazy() por feature
│       ├── test/                   # setup de Vitest + handlers MSW
│       │   ├── setup.ts
│       │   └── msw/{server.ts,handlers.ts}
│       ├── core/                   # Infraestructura transversal (sin UI de negocio)
│       │   ├── config/env.ts       # lee window.__APP_CONFIG__ / import.meta.env
│       │   ├── auth/sesion.ts      # OIDC + PKCE, token solo en memoria
│       │   ├── http/
│       │   │   ├── client.ts       # openapi-fetch tipado + interceptores
│       │   │   ├── api-error.ts    # ApiError a partir de problem+json
│       │   │   └── schema.d.ts     # GENERADO desde OpenAPI (no editar)
│       │   └── logging/logger.ts
│       ├── shared/                 # Reutilizable y agnóstico al dominio
│       │   ├── ui/                 # Button, Card, Spinner, Alert, FileDrop...
│       │   ├── hooks/              # useMediaQuery, useObjectUrl...
│       │   └── lib/                # formatters, cn(), etc.
│       └── features/               # Screaming Architecture: el árbol "grita" el negocio
│           ├── diagnostico/
│           │   ├── api/diagnostico.api.ts      # llamadas HTTP de la feature
│           │   ├── model/
│           │   │   ├── schemas.ts              # Zod: formulario + parseo de respuesta
│           │   │   └── types.ts
│           │   ├── hooks/useDiagnosticar.ts    # TanStack Query mutation
│           │   ├── components/
│           │   │   ├── SelectorOrgano.tsx
│           │   │   ├── CapturaImagen.tsx
│           │   │   └── VisorDetecciones.tsx    # dibuja cajas sobre la foto
│           │   ├── pages/DiagnosticoPage.tsx
│           │   └── index.ts                    # API pública de la feature
│           ├── historial/          # misma forma
│           └── catalogo/           # misma forma
│
├── ml/                             # Todo lo de entrenamiento (fuera de los contenedores)
│   ├── notebooks/train_yolo11_object_detection_on_custom_dataset.ipynb
│   ├── scripts/                    # 01_galeria_fruto_sano.py, 02_preparar_datasets.py, comun.py
│   ├── datasets/                   # DatasetOriginal, DatasetHojas, DatasetFrutos (git-ignored)
│   └── ESTRATEGIA_DATASET.md
│
├── docs/
│   ├── ARQUITECTURA.md             # este documento
│   └── adr/                        # Architecture Decision Records (0001-monorepo.md, ...)
├── docker-compose.yml              # orquestación local
├── docker-compose.override.yml     # hot-reload en desarrollo
├── .env.example
├── Makefile                        # make lint / test / gen-api / up
├── .pre-commit-config.yaml         # ruff, mypy, eslint, prettier
└── .github/workflows/ci.yml        # lint + tests + chequeo de drift del contrato API
```

> **Migración desde el estado actual:** mover `scripts/`, `revision/`, los `Dataset*/` y el notebook a `ml/`; copiar `bestHojas.pt` a `backend/models/hojas.pt`.

### Regla de dependencias

```
            api  ──►  application  ──►  domain
             │             ▲
             ▼             │ (implementa ports)
        container  ──►  infrastructure
```

- `domain` no importa nada del proyecto ni frameworks (ni FastAPI, ni SQLAlchemy, ni Ultralytics).
- `application` importa solo `domain` y define **puertos** (interfaces).
- `infrastructure` implementa puertos; puede importar `application` y `domain`.
- `api` importa `application` (casos de uso y DTOs) y nunca `infrastructure`.
- `container.py` es el **único** sitio que importa clases concretas de `infrastructure`.
- Un módulo no importa el interior de otro módulo; si `diagnostico` necesita datos de `catalogo`, lo hace a través de un puerto propio (§C.1).

Estas reglas se **verifican en CI** con `import-linter`:

```toml
# backend/pyproject.toml
[tool.importlinter]
root_package = "plagas"

[[tool.importlinter.contracts]]
name = "Capas hexagonales"
type = "layers"
containers = ["plagas.modules.diagnostico", "plagas.modules.catalogo"]
layers = ["api", "infrastructure", "application", "domain"]

[[tool.importlinter.contracts]]
name = "La API no conoce la infraestructura"
type = "forbidden"
source_modules = ["plagas.modules.*.api"]
forbidden_modules = ["plagas.modules.*.infrastructure"]

[[tool.importlinter.contracts]]
name = "Dominio puro"
type = "forbidden"
source_modules = ["plagas.modules.*.domain", "plagas.shared.domain"]
forbidden_modules = ["fastapi", "sqlalchemy", "ultralytics", "pydantic"]

[[tool.importlinter.contracts]]
name = "Módulos independientes"
type = "independence"
modules = ["plagas.modules.diagnostico", "plagas.modules.catalogo"]
```

---

## B. Principios SOLID aplicados

### B.1 Capa de dominio (base de los ejemplos)

```python
# modules/diagnostico/domain/value_objects.py
from dataclasses import dataclass
from enum import StrEnum

from .errors import ConfianzaInvalida, ImagenInvalida

MIME_PERMITIDOS = frozenset({"image/jpeg", "image/png", "image/webp"})
TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024


class Organo(StrEnum):
    HOJA = "hoja"
    FRUTO = "fruto"


@dataclass(frozen=True, slots=True)
class Confianza:
    valor: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.valor <= 1.0:
            raise ConfianzaInvalida(self.valor)


@dataclass(frozen=True, slots=True)
class CajaDelimitadora:
    """Coordenadas normalizadas (0..1) para ser independientes de la resolución."""
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True, slots=True)
class Deteccion:
    clase: str
    confianza: Confianza
    caja: CajaDelimitadora

    @property
    def es_sana(self) -> bool:
        return self.clase.endswith(("_sana", "_sano"))


@dataclass(frozen=True, slots=True)
class Imagen:
    contenido: bytes
    tipo_mime: str

    def __post_init__(self) -> None:
        if self.tipo_mime not in MIME_PERMITIDOS:
            raise ImagenInvalida(f"Formato no soportado: {self.tipo_mime}")
        if not self.contenido:
            raise ImagenInvalida("La imagen está vacía")
        if len(self.contenido) > TAMANO_MAXIMO_BYTES:
            raise ImagenInvalida("La imagen supera 10 MB")
```

```python
# modules/diagnostico/domain/entities.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from ....shared.domain.identidad import Usuario
from .value_objects import Deteccion, Organo


@dataclass(slots=True)
class Diagnostico:
    id: UUID
    propietario_id: str
    organo: Organo
    imagen_ref: str
    creado_en: datetime
    detecciones: tuple[Deteccion, ...] = field(default_factory=tuple)

    @classmethod
    def registrar(
        cls, *, id: UUID, propietario_id: str, organo: Organo, imagen_ref: str,
        detecciones: list[Deteccion], umbral: float, ahora: datetime,
    ) -> "Diagnostico":
        filtradas = tuple(d for d in detecciones if d.confianza.valor >= umbral)
        return cls(id=id, propietario_id=propietario_id, organo=organo,
                   imagen_ref=imagen_ref, creado_en=ahora, detecciones=filtradas)

    def visible_para(self, usuario: "Usuario") -> bool:
        return self.propietario_id == usuario.id or usuario.puede_ver_todo

    @property
    def enfermedades(self) -> list[str]:
        return sorted({d.clase for d in self.detecciones if not d.es_sana})

    @property
    def es_sano(self) -> bool:
        return not self.enfermedades
```

```python
# shared/domain/errors.py
class ErrorDominio(Exception):
    """Base de errores de negocio. 'codigo' es estable y lo consume el frontend."""
    codigo: str = "error_dominio"

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje

class NoAutenticado(ErrorDominio):
    codigo = "no_autenticado"

class SinPermiso(ErrorDominio):
    codigo = "sin_permiso"

class LimiteExcedido(ErrorDominio):
    codigo = "limite_excedido"

# modules/diagnostico/domain/errors.py
class ImagenInvalida(ErrorDominio):
    codigo = "imagen_invalida"

class OrganoNoSoportado(ErrorDominio):
    codigo = "organo_no_soportado"

class DiagnosticoNoEncontrado(ErrorDominio):
    codigo = "diagnostico_no_encontrado"

class ConfianzaInvalida(ErrorDominio):
    codigo = "confianza_invalida"
    def __init__(self, valor: float) -> None:
        super().__init__(f"Confianza fuera de rango: {valor}")
```

### B.2 SRP — transporte HTTP separado de la lógica de negocio

Cada pieza tiene **una sola razón para cambiar**:

| Pieza | Responsabilidad única | Cambia cuando... |
|---|---|---|
| `api/router.py` | Traducir HTTP ⇄ Command/DTO | cambia el contrato HTTP |
| `api/schemas.py` | Forma JSON pública | cambia el contrato HTTP |
| `use_cases/diagnosticar_imagen.py` | Orquestar el flujo de diagnóstico | cambia la regla de negocio |
| `domain/entities.py` | Invariantes del diagnóstico | cambia el concepto de "sano/enfermo" |
| `infrastructure/yolo_detector.py` | Ejecutar YOLO y mapear su salida | cambia la librería de ML |
| `infrastructure/repositorio_sqlalchemy.py` | Persistir/leer diagnósticos | cambia la BD |

El router **no** valida reglas de negocio, no llama a YOLO, ni abre sesiones de BD:

```python
# modules/diagnostico/api/router.py
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from ....shared.api.auth import get_usuario_actual
from ....shared.api.seguridad import limiter
from ....shared.domain.identidad import Usuario
from ..application.dtos import DiagnosticarImagenCommand
from ..application.use_cases.diagnosticar_imagen import DiagnosticarImagen
from ..application.use_cases.obtener_diagnostico import ObtenerDiagnostico
from ..domain.value_objects import Organo
from .dependencies import get_diagnosticar_imagen, get_obtener_diagnostico
from .schemas import DiagnosticoResponse

router = APIRouter(prefix="/diagnosticos", tags=["diagnosticos"])
UsuarioActual = Annotated[Usuario, Depends(get_usuario_actual)]


@router.post("", response_model=DiagnosticoResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")          # la inferencia es costosa (§E.4)
async def crear_diagnostico(
    request: Request,                 # requerido por slowapi
    organo: Annotated[Organo, Form()],
    imagen: Annotated[UploadFile, File()],
    usuario: UsuarioActual,
    caso_uso: Annotated[DiagnosticarImagen, Depends(get_diagnosticar_imagen)],
) -> DiagnosticoResponse:
    # El tamaño del cuerpo ya fue limitado por LimiteCuerpoMiddleware (§E.2)
    comando = DiagnosticarImagenCommand(
        propietario_id=usuario.id,
        organo=organo,
        contenido=await imagen.read(),
        tipo_mime=imagen.content_type or "",
    )
    resultado = await caso_uso.ejecutar(comando)
    return DiagnosticoResponse.model_validate(resultado, from_attributes=True)


@router.get("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def obtener_diagnostico(
    diagnostico_id: UUID,
    usuario: UsuarioActual,
    caso_uso: Annotated[ObtenerDiagnostico, Depends(get_obtener_diagnostico)],
) -> DiagnosticoResponse:
    resultado = await caso_uso.ejecutar(diagnostico_id, usuario)
    return DiagnosticoResponse.model_validate(resultado, from_attributes=True)
```

El caso de uso no sabe nada de HTTP:

```python
# modules/diagnostico/application/use_cases/diagnosticar_imagen.py
from ...domain.entities import Diagnostico
from ...domain.value_objects import Imagen
from ....shared.domain.ports import GeneradorId, Reloj
from ..dtos import DiagnosticarImagenCommand, DiagnosticoDTO
from ..ports import AlmacenImagenes, EscrituraDiagnosticos, InspectorImagenes, ProveedorDetectores


class DiagnosticarImagen:
    def __init__(
        self,
        inspector: InspectorImagenes,
        detectores: ProveedorDetectores,
        almacen: AlmacenImagenes,
        repositorio: EscrituraDiagnosticos,
        reloj: Reloj,
        ids: GeneradorId,
        umbral_confianza: float,
    ) -> None:
        self._inspector = inspector
        self._detectores = detectores
        self._almacen = almacen
        self._repositorio = repositorio
        self._reloj = reloj
        self._ids = ids
        self._umbral = umbral_confianza

    async def ejecutar(self, cmd: DiagnosticarImagenCommand) -> DiagnosticoDTO:
        recibida = Imagen(contenido=cmd.contenido, tipo_mime=cmd.tipo_mime)
        detector = self._detectores.para(cmd.organo)        # OrganoNoSoportado si no existe
        imagen = await self._inspector.sanear(recibida)     # magic bytes, bombas, sin EXIF (§E.2)
        detecciones = await detector.detectar(imagen)
        imagen_ref = await self._almacen.guardar(imagen)

        diagnostico = Diagnostico.registrar(
            id=self._ids.nuevo(),
            propietario_id=cmd.propietario_id,
            organo=cmd.organo,
            imagen_ref=imagen_ref,
            detecciones=detecciones,
            umbral=self._umbral,
            ahora=self._reloj.ahora(),
        )
        await self._repositorio.guardar(diagnostico)
        return DiagnosticoDTO.desde_entidad(diagnostico)
```

### B.3 OCP — extender sin modificar

**Caso 1: añadir un nuevo órgano/modelo (p. ej. `tallo`)**
El caso de uso pide un detector a `ProveedorDetectores` por órgano; no tiene `if organo == ...`. Añadir un modelo es:
1. Agregar `TALLO = "tallo"` a `Organo` (vocabulario del dominio).
2. Poner `tallo.pt` en `models/` y añadir la entrada en `MODELOS_POR_ORGANO` (configuración).
Ni `DiagnosticarImagen`, ni el router, ni el repositorio se tocan.

```python
# modules/diagnostico/infrastructure/registro_detectores.py
from ..application.ports import DetectorEnfermedades
from ..domain.errors import OrganoNoSoportado
from ..domain.value_objects import Organo


class RegistroDetectores:
    """Implementa ProveedorDetectores. Se arma una sola vez en el container."""

    def __init__(self, detectores: dict[Organo, DetectorEnfermedades]) -> None:
        self._detectores = dict(detectores)

    def para(self, organo: Organo) -> DetectorEnfermedades:
        try:
            return self._detectores[organo]
        except KeyError:
            raise OrganoNoSoportado(f"No hay modelo cargado para '{organo}'") from None
```

**Caso 2: cambiar el motor de inferencia** (ONNX Runtime, TensorRT, un microservicio de inferencia remoto): se crea `DetectorOnnx` / `DetectorRemotoHttp` que cumpla `DetectorEnfermedades` y se cambia una línea en `container.py`.

**Caso 3: nuevo caso de uso** (p. ej. `ExportarHistorialCsv`): nuevo archivo en `use_cases/`, nuevo endpoint en el router, nueva función en `dependencies.py`. Nada existente se modifica salvo el registro.

**Caso 4: nuevo módulo completo:** ver §C.1; se registra con una línea en `main.py`.

### B.4 LSP & ISP — contratos pequeños y sustituibles

Los puertos se definen con `typing.Protocol` (tipado estructural: los adapters no heredan, solo cumplen la forma, y `mypy --strict` lo verifica). Se separan por **rol del consumidor**, no por tabla:

```python
# modules/diagnostico/application/ports.py
from typing import Protocol
from uuid import UUID

from ..domain.entities import Diagnostico
from ..domain.value_objects import Deteccion, Imagen, Organo


class InspectorImagenes(Protocol):
    async def sanear(self, imagen: Imagen) -> Imagen: ...         # ImagenInvalida si no es segura


class DetectorEnfermedades(Protocol):
    async def detectar(self, imagen: Imagen) -> list[Deteccion]: ...


class ProveedorDetectores(Protocol):
    def para(self, organo: Organo) -> DetectorEnfermedades: ...


class AlmacenImagenes(Protocol):
    async def guardar(self, imagen: Imagen) -> str: ...          # devuelve referencia opaca
    async def url_publica(self, referencia: str) -> str: ...


# ISP: quien solo escribe no depende de métodos de consulta, y viceversa
class EscrituraDiagnosticos(Protocol):
    async def guardar(self, diagnostico: Diagnostico) -> None: ...


class LecturaDiagnosticos(Protocol):
    async def por_id(self, id: UUID) -> Diagnostico | None: ...
    async def recientes(self, limite: int, desplazamiento: int) -> list[Diagnostico]: ...
```

```python
# shared/domain/ports.py
from datetime import datetime
from typing import Protocol
from uuid import UUID

class Reloj(Protocol):
    def ahora(self) -> datetime: ...

class GeneradorId(Protocol):
    def nuevo(self) -> UUID: ...

class VerificadorTokens(Protocol):
    def verificar(self, token: str) -> Usuario: ...    # NoAutenticado si no es válido
```

**Reglas LSP** que todo adapter debe respetar (y que se prueban con una *suite de contrato* compartida en `tests/contract/`, ejecutada contra el fake y contra el adapter real):

- `detectar` devuelve cajas **normalizadas 0..1** y nunca lanza excepciones de la librería: las traduce a `ErrorDominio` o a `ErrorInfraestructura`.
- `por_id` devuelve `None` si no existe (no lanza); el caso de uso decide lanzar `DiagnosticoNoEncontrado`.
- `guardar` es idempotente por `id`.

Adapter real del detector:

```python
# modules/diagnostico/infrastructure/yolo_detector.py
import io
import threading
from pathlib import Path

import anyio
from PIL import Image as PILImage
from ultralytics import YOLO

from ..domain.value_objects import CajaDelimitadora, Confianza, Deteccion, Imagen


class DetectorYolo:
    """Cumple DetectorEnfermedades. Un modelo cargado por proceso, inferencia en un hilo."""

    def __init__(self, ruta_pesos: Path, imgsz: int = 1024, conf_minima: float = 0.10) -> None:
        self._modelo = YOLO(str(ruta_pesos))
        self._imgsz = imgsz
        self._conf_minima = conf_minima
        self._lock = threading.Lock()  # predict() de Ultralytics no es thread-safe

    async def detectar(self, imagen: Imagen) -> list[Deteccion]:
        # La inferencia es CPU/GPU-bound: no bloquear el event loop
        return await anyio.to_thread.run_sync(self._predecir, imagen.contenido)

    def _predecir(self, contenido: bytes) -> list[Deteccion]:
        pil = PILImage.open(io.BytesIO(contenido)).convert("RGB")
        with self._lock:
            resultado = self._modelo.predict(
                pil, imgsz=self._imgsz, conf=self._conf_minima, verbose=False
            )[0]
        nombres = resultado.names
        cajas = resultado.boxes
        return [
            Deteccion(
                clase=nombres[int(cls)],
                confianza=Confianza(float(conf)),
                caja=CajaDelimitadora(*map(float, xyxyn)),
            )
            for xyxyn, conf, cls in zip(
                cajas.xyxyn.tolist(), cajas.conf.tolist(), cajas.cls.tolist()
            )
        ]
```

Fake para tests unitarios (sustituible por LSP, sin YOLO ni GPU):

```python
# tests/unit/fakes.py
class DetectorFalso:
    def __init__(self, detecciones: list[Deteccion]) -> None:
        self.detecciones = detecciones
        self.llamadas = 0

    async def detectar(self, imagen: Imagen) -> list[Deteccion]:
        self.llamadas += 1
        return list(self.detecciones)
```

### B.5 DIP — inyección de dependencias

Las capas altas (casos de uso) dependen de **abstracciones** (`Protocol`); las concretas se eligen en un **Composition Root** (`container.py`). Se usa DI manual + `Depends` de FastAPI: es explícito, sin magia, y suficiente para el tamaño del proyecto. (Si crece mucho, se puede migrar a `dependency-injector` o `svcs` sin tocar casos de uso.)

```python
# config.py
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    env: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"
    database_url: str
    cors_origins: list[str] = ["http://localhost:5173"]

    modelos_dir: Path = Path("models")
    modelo_hojas: str = "hojas.pt"
    modelo_frutos: str = "frutos.pt"
    yolo_imgsz: int = 1024
    umbral_confianza: float = 0.35

    almacen: Literal["local", "s3"] = "local"
    almacen_local_dir: Path = Path("/data/imagenes")
    s3_bucket: str | None = None

    # Seguridad (§E)
    oidc_emisor: str                        # p. ej. https://auth.plagas-palta.app/realms/plagas
    oidc_audiencia: str = "api-plagas"
    oidc_jwks_url: str
    hosts_permitidos: list[str] = ["localhost", "127.0.0.1"]
    max_cuerpo_bytes: int = 11 * 1024 * 1024     # 10 MB de imagen + overhead multipart
    rate_limit_storage: str = "memory://"        # redis://redis:6379/0 con varias réplicas (lo lee slowapi)
    sha256_modelo_hojas: str
    sha256_modelo_frutos: str
```

```python
# container.py — único archivo que conoce las clases concretas
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import async_sessionmaker

from .config import Settings
from .modules.diagnostico.application.use_cases.diagnosticar_imagen import DiagnosticarImagen
from .modules.diagnostico.application.use_cases.obtener_diagnostico import ObtenerDiagnostico
from .modules.diagnostico.domain.value_objects import Organo
from .modules.diagnostico.infrastructure.almacen_local import AlmacenLocal
from .modules.diagnostico.infrastructure.almacen_s3 import AlmacenS3
from .modules.diagnostico.infrastructure.inspector_pillow import InspectorImagenesPillow
from .modules.diagnostico.infrastructure.registro_detectores import RegistroDetectores
from .modules.diagnostico.infrastructure.repositorio_sqlalchemy import RepositorioDiagnosticosSql
from .modules.diagnostico.infrastructure.yolo_detector import DetectorYolo
from .shared.infrastructure.db import crear_engine
from .shared.infrastructure.integridad import verificar_sha256
from .shared.infrastructure.oidc import VerificadorJwtOidc
from .shared.infrastructure.reloj import GeneradorUuid4, RelojSistema


@dataclass
class Container:
    settings: Settings
    sesiones: async_sessionmaker
    inspector: InspectorImagenesPillow
    detectores: RegistroDetectores
    almacen: AlmacenLocal | AlmacenS3
    verificador_tokens: VerificadorJwtOidc
    reloj: RelojSistema
    ids: GeneradorUuid4

    @classmethod
    def construir(cls, settings: Settings) -> "Container":
        modelos = {
            Organo.HOJA: (settings.modelos_dir / settings.modelo_hojas, settings.sha256_modelo_hojas),
            Organo.FRUTO: (settings.modelos_dir / settings.modelo_frutos, settings.sha256_modelo_frutos),
        }
        for ruta, sha in modelos.values():
            verificar_sha256(ruta, sha)          # antes de deserializar (pickle) — §E.7
        detectores = RegistroDetectores(
            {organo: DetectorYolo(ruta, imgsz=settings.yolo_imgsz) for organo, (ruta, _) in modelos.items()}
        )
        almacen = (
            AlmacenS3(settings.s3_bucket) if settings.almacen == "s3"
            else AlmacenLocal(settings.almacen_local_dir)
        )
        return cls(
            settings=settings,
            sesiones=async_sessionmaker(crear_engine(settings.database_url), expire_on_commit=False),
            inspector=InspectorImagenesPillow(),
            detectores=detectores,
            almacen=almacen,
            verificador_tokens=VerificadorJwtOidc(
                emisor=settings.oidc_emisor,
                audiencia=settings.oidc_audiencia,
                jwks_url=settings.oidc_jwks_url,
            ),
            reloj=RelojSistema(),
            ids=GeneradorUuid4(),
        )

    # Fábricas de casos de uso (objetos ligeros, uno por request)
    def diagnosticar_imagen(self, sesion) -> DiagnosticarImagen:
        return DiagnosticarImagen(
            inspector=self.inspector,
            detectores=self.detectores,
            almacen=self.almacen,
            repositorio=RepositorioDiagnosticosSql(sesion),
            reloj=self.reloj,
            ids=self.ids,
            umbral_confianza=self.settings.umbral_confianza,
        )

    def obtener_diagnostico(self, sesion) -> ObtenerDiagnostico:
        return ObtenerDiagnostico(lectura=RepositorioDiagnosticosSql(sesion))
```

```python
# modules/diagnostico/api/dependencies.py
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....shared.api.dependencias import get_container


async def get_sesion(container=Depends(get_container)) -> AsyncIterator[AsyncSession]:
    async with container.sesiones() as sesion, sesion.begin():   # unidad de trabajo por request
        yield sesion


def get_diagnosticar_imagen(
    container=Depends(get_container),
    sesion: Annotated[AsyncSession, Depends(get_sesion)] = None,
):
    return container.diagnosticar_imagen(sesion)


def get_obtener_diagnostico(
    container=Depends(get_container),
    sesion: Annotated[AsyncSession, Depends(get_sesion)] = None,
):
    return container.obtener_diagnostico(sesion)
```

```python
# main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import Settings
from .container import Container
from .modules.catalogo.api.router import router as catalogo_router
from .modules.diagnostico.api.router import router as diagnostico_router
from .shared.api.errors import registrar_manejadores_error
from .shared.api.health import router as health_router
from .shared.api.middlewares import RequestContextMiddleware
from .shared.api.seguridad import (
    CabecerasSeguridadMiddleware, LimiteCuerpoMiddleware, configurar_rate_limit,
)
from .shared.infrastructure.logging import configurar_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configurar_logging(settings.log_level, json=settings.env != "dev")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.container = Container.construir(settings)   # carga modelos YOLO una sola vez
        yield

    es_prod = settings.env == "prod"
    app = FastAPI(title="API Plagas Palta Hass", version="1.0.0", lifespan=lifespan,
                  docs_url=None if es_prod else "/docs",
                  redoc_url=None, openapi_url=None if es_prod else "/openapi.json")

    # El último middleware añadido es el más externo: el límite de cuerpo corta primero
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(CabecerasSeguridadMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_methods=["GET", "POST", "DELETE"],
                       allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
                       expose_headers=["X-Request-ID"])
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.hosts_permitidos)
    app.add_middleware(LimiteCuerpoMiddleware, maximo_bytes=settings.max_cuerpo_bytes)
    configurar_rate_limit(app)
    registrar_manejadores_error(app)

    app.include_router(health_router)
    for router in (diagnostico_router, catalogo_router):     # OCP: nuevo módulo = una línea
        app.include_router(router, prefix="/api/v1")
    return app
```

> Se usa el patrón *factory* (`uvicorn plagas.main:create_app --factory`) en lugar de una variable global `app = create_app()`: importar `plagas.main` en los tests no lee variables de entorno ni intenta cargar los modelos.

En tests, se sustituye cualquier dependencia sin tocar producción:

```python
app.dependency_overrides[get_diagnosticar_imagen] = lambda: DiagnosticarImagen(
    inspector=InspectorQueAcepta(),
    detectores=ProveedorDetectoresFalso({Organo.HOJA: DetectorFalso([...])}),
    almacen=AlmacenEnMemoria(), repositorio=RepoEnMemoria(),
    reloj=RelojFijo(), ids=IdsSecuenciales(), umbral_confianza=0.35,
)
```

(Ejemplos completos en §F.)

### B.6 SOLID en el frontend

| Principio | Aplicación |
|---|---|
| **SRP** | `components/` solo presentan; `hooks/` manejan estado de servidor (TanStack Query); `api/` solo hace HTTP; `model/` valida (Zod). |
| **OCP** | Nueva feature = nueva carpeta en `features/` + una ruta `lazy()` en `app/router.tsx`. |
| **ISP** | Componentes con props mínimas (`VisorDetecciones` recibe `detecciones` y `src`, no el diagnóstico completo). |
| **DIP** | Las features dependen de `core/http/client.ts` (abstracción), no de `fetch`/axios directamente; en tests se inyecta MSW. |

Fronteras verificadas con `eslint-plugin-boundaries`:

```js
// eslint.config.js (extracto)
'boundaries/element-types': ['error', {
  default: 'disallow',
  rules: [
    { from: 'app',      allow: ['features', 'shared', 'core'] },
    { from: 'features', allow: ['shared', 'core', ['features', { feature: '${from.feature}' }]] },
    { from: 'shared',   allow: ['shared'] },
    { from: 'core',     allow: ['core'] },
  ],
}],
// Otras features solo se consumen vía su index.ts público
'boundaries/entry-point': ['error', { default: 'disallow',
  rules: [{ target: ['features'], allow: 'index.ts' }] }],
```

---

## C. Modularidad y escalabilidad

### C.1 Convención para crear un módulo nuevo

**Backend** (ejemplo: módulo `alertas` para avisar brotes por zona):

1. Crear `src/plagas/modules/alertas/{domain,application/use_cases,infrastructure,api}/` con `__init__.py`.
2. **Dominio primero:** entidades y value objects con tests unitarios puros.
3. **Puertos** en `application/ports.py`, solo los métodos que los casos de uso necesitan.
4. **Casos de uso**: una clase por caso, método `ejecutar(cmd) -> DTO`, probados con fakes.
5. **Adapters** en `infrastructure/` + tabla en `orm.py` + migración Alembic (`alembic revision --autogenerate -m "alertas"`).
6. **API**: `schemas.py`, `router.py` (prefijo propio), `dependencies.py`.
7. **Cablear**: fábricas en `container.py` + `include_router` en `main.py` + añadir el módulo a los contratos de `import-linter`.
8. Si necesita datos de otro módulo: definir un puerto propio (p. ej. `ConsultaDiagnosticosPorZona`) y un adapter en `alertas/infrastructure/` que llame al caso de uso público del otro módulo. Nunca importar sus repos o entidades.

Nomenclatura:

| Elemento | Convención | Ejemplo |
|---|---|---|
| Caso de uso | Verbo + sustantivo, `PascalCase` | `DiagnosticarImagen` |
| Puerto | Rol, sin prefijo `I` | `LecturaDiagnosticos` |
| Adapter | Tecnología + rol | `RepositorioDiagnosticosSql`, `DetectorYolo` |
| Command/Query | `<CasoUso>Command` / `<CasoUso>Query` | `DiagnosticarImagenCommand` |
| Schema HTTP | `<Recurso>Request` / `<Recurso>Response` | `DiagnosticoResponse` |
| Endpoint | plural, kebab-case, versionado | `POST /api/v1/diagnosticos` |

**Frontend** (ejemplo: feature `alertas`):

1. `src/features/alertas/{api,model,hooks,components,pages}/` + `index.ts`.
2. Regenerar tipos (`npm run gen:api`) para obtener los nuevos endpoints tipados.
3. `api/alertas.api.ts` usa `apiClient` de `core/http`.
4. `model/schemas.ts` con Zod para formularios y parseo de respuestas.
5. `hooks/` con `useQuery`/`useMutation` y *query keys* propias (`['alertas', ...]`).
6. Exportar solo la página y lo público en `index.ts`; registrar la ruta con `lazy()` en `app/router.tsx`.

### C.2 Manejo centralizado de errores

**Backend → RFC 9457 (`application/problem+json`)**. El dominio lanza `ErrorDominio` con `codigo`; la capa API decide el status HTTP en un único mapa:

```python
# shared/api/errors.py
import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..domain.errors import ErrorDominio, LimiteExcedido, NoAutenticado, SinPermiso
from ...modules.diagnostico.domain import errors as diag

log = structlog.get_logger()

STATUS_POR_ERROR: dict[type[ErrorDominio], int] = {
    NoAutenticado: 401,
    SinPermiso: 403,
    LimiteExcedido: 429,
    diag.ImagenInvalida: 422,
    diag.OrganoNoSoportado: 422,
    diag.DiagnosticoNoEncontrado: 404,
}


def _problema(status: int, codigo: str, detalle: str, request: Request, **extra) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"https://plagas-palta.app/errores/{codigo}",
            "title": codigo,
            "status": status,
            "detail": detalle,
            "instance": request.url.path,
            "request_id": getattr(request.state, "request_id", None),
            **extra,
        },
    )


def registrar_manejadores_error(app: FastAPI) -> None:
    @app.exception_handler(ErrorDominio)
    async def _dominio(request: Request, exc: ErrorDominio):
        status = next((s for t, s in STATUS_POR_ERROR.items() if isinstance(exc, t)), 400)
        log.info("error_dominio", codigo=exc.codigo, status=status)
        respuesta = _problema(status, exc.codigo, exc.mensaje, request)
        if status == 401:
            respuesta.headers["WWW-Authenticate"] = "Bearer"
        return respuesta

    @app.exception_handler(RequestValidationError)
    async def _validacion(request: Request, exc: RequestValidationError):
        return _problema(422, "validacion", "Datos de entrada inválidos", request,
                         errors=exc.errors())

    @app.exception_handler(Exception)
    async def _inesperado(request: Request, exc: Exception):
        log.exception("error_no_controlado")
        return _problema(500, "error_interno", "Ocurrió un error inesperado", request)
```

**Frontend:** `core/http/api-error.ts` convierte cualquier `problem+json` en `ApiError { status, codigo, detalle, requestId }`. Las features muestran mensajes por `codigo` (estable), nunca por texto del backend. Un `ErrorBoundary` global captura errores de render y un `QueryCache.onError` global registra los errores de red.

```ts
// core/http/api-error.ts
import { z } from 'zod';

const ProblemSchema = z.object({
  title: z.string(),
  status: z.number(),
  detail: z.string(),
  request_id: z.string().optional(),
});

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly codigo: string,
    public readonly detalle: string,
    public readonly requestId?: string,
  ) {
    super(detalle);
  }

  static desde(body: unknown, status: number): ApiError {
    const p = ProblemSchema.safeParse(body);
    return p.success
      ? new ApiError(p.data.status, p.data.title, p.data.detail, p.data.request_id)
      : new ApiError(status, 'desconocido', 'Error de comunicación con el servidor');
  }
}
```

### C.3 Logs estructurados

- **Backend:** `structlog` con salida JSON en staging/prod y consola legible en dev. `RequestContextMiddleware` genera/propaga `X-Request-ID` y lo enlaza con `structlog.contextvars`, de modo que todas las líneas de un request comparten `request_id`.
- Campos estándar: `timestamp`, `level`, `event`, `request_id`, `path`, `method`, `status`, `duracion_ms`, y en diagnósticos `organo`, `n_detecciones`, `modelo_version`, `inferencia_ms`.
- **Nunca** se loguean los bytes de la imagen ni datos personales.
- **Frontend:** `core/logging/logger.ts` envuelve `console` en dev y, en prod, envía errores a Sentry (u otro) incluyendo el `requestId` de `ApiError` para correlacionar con el backend.

```python
# shared/api/middlewares.py
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        inicio = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        structlog.get_logger().info(
            "http_request", method=request.method, path=request.url.path,
            status=response.status_code,
            duracion_ms=round((time.perf_counter() - inicio) * 1000, 1),
        )
        return response
```

### C.4 Validación de esquemas

| Dónde | Herramienta | Qué valida |
|---|---|---|
| Borde HTTP backend | Pydantic (`schemas.py`, `Form`, `File`) | Forma y tipos del request/response |
| Dominio backend | `__post_init__` de value objects | Invariantes de negocio (MIME, tamaño, rango de confianza) |
| Configuración | `pydantic-settings` | Variables de entorno al arrancar (falla rápido) |
| Formularios frontend | Zod + react-hook-form | Órgano elegido, archivo imagen, tamaño ≤ 10 MB |
| Respuestas en frontend | Tipos OpenAPI (compilación) + Zod en respuestas críticas (runtime) | Que el backend cumple el contrato |

```python
# modules/diagnostico/api/schemas.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..domain.value_objects import Organo


class CajaSchema(BaseModel):
    x1: float = Field(ge=0, le=1)
    y1: float = Field(ge=0, le=1)
    x2: float = Field(ge=0, le=1)
    y2: float = Field(ge=0, le=1)


class DeteccionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    clase: str
    confianza: float = Field(ge=0, le=1)
    caja: CajaSchema


class DiagnosticoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organo: Organo
    es_sano: bool
    enfermedades: list[str]
    detecciones: list[DeteccionSchema]
    imagen_url: str
    creado_en: datetime
```

```ts
// features/diagnostico/model/schemas.ts
import { z } from 'zod';

export const ORGANOS = ['hoja', 'fruto'] as const;
const MAX_BYTES = 10 * 1024 * 1024;

export const DiagnosticoFormSchema = z.object({
  organo: z.enum(ORGANOS),
  imagen: z
    .instanceof(File)
    .refine((f) => ['image/jpeg', 'image/png', 'image/webp'].includes(f.type), 'Formato no soportado')
    .refine((f) => f.size <= MAX_BYTES, 'La imagen supera 10 MB'),
});
export type DiagnosticoForm = z.infer<typeof DiagnosticoFormSchema>;
```

### C.5 Contrato API entre backend y frontend

Estrategia **contract-first desde el código**: FastAPI es la fuente de verdad del contrato y el frontend genera sus tipos.

1. El backend expone `/openapi.json` (y un script `python -m plagas.scripts.exportar_openapi > openapi.json` que no necesita levantar el servidor ni cargar YOLO).
2. `openapi.json` se **versiona** en la raíz del monorepo: cualquier cambio de contrato aparece en el diff del PR.
3. El frontend genera tipos con `openapi-typescript` y usa `openapi-fetch` (cliente de ~6 KB, totalmente tipado):

```jsonc
// frontend/package.json (scripts)
{
  "gen:api": "openapi-typescript ../openapi.json -o src/core/http/schema.d.ts",
  "check:api": "npm run gen:api && git diff --exit-code src/core/http/schema.d.ts"
}
```

```ts
// core/http/client.ts
import createClient, { type Middleware } from 'openapi-fetch';
import type { paths } from './schema';
import { env } from '../config/env';
import { ApiError } from './api-error';

const errores: Middleware = {
  async onResponse({ response }) {
    if (!response.ok) {
      const body = await response.clone().json().catch(() => null);
      throw ApiError.desde(body, response.status);
    }
  },
};

export const apiClient = createClient<paths>({ baseUrl: env.apiBaseUrl });
apiClient.use(errores);
```

```ts
// features/diagnostico/api/diagnostico.api.ts
import { apiClient } from '@/core/http/client';
import type { DiagnosticoForm } from '../model/schemas';

export async function crearDiagnostico({ organo, imagen }: DiagnosticoForm) {
  const { data } = await apiClient.POST('/api/v1/diagnosticos', {
    body: { organo, imagen } as never,          // multipart: se serializa abajo
    bodySerializer: (b) => {
      const fd = new FormData();
      fd.append('organo', organo);
      fd.append('imagen', imagen);
      return fd;
    },
  });
  return data!;
}
```

```ts
// features/diagnostico/hooks/useDiagnosticar.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { crearDiagnostico } from '../api/diagnostico.api';

export function useDiagnosticar() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: crearDiagnostico,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['historial'] }),
  });
}
```

4. **CI** falla si el `openapi.json` exportado difiere del versionado o si `schema.d.ts` no está regenerado (`npm run check:api`), evitando que backend y frontend se desincronicen.
5. **Versionado:** prefijo `/api/v1`. Cambios incompatibles → `/api/v2` conviviendo un tiempo con v1. Campos nuevos opcionales no requieren nueva versión.

### C.6 Escalabilidad

- **Inferencia:** YOLO se carga **una vez por proceso** en el `lifespan`. Se usa **1 worker Uvicorn por contenedor** y se escala horizontalmente (réplicas), porque cada worker duplicaría los modelos en memoria.
- Si la inferencia se vuelve el cuello de botella: extraer `DetectorEnfermedades` a un servicio dedicado (Triton / un FastAPI de inferencia con GPU) y cambiar el adapter por `DetectorRemotoHttp`. El resto del sistema no cambia (DIP/OCP).
- Si hace falta asincronía (fotos en lote): un caso de uso `EncolarDiagnostico` + cola (Redis/ARQ) + worker que reutiliza `DiagnosticarImagen`.
- **Imágenes:** en prod se guardan en S3/MinIO (`AlmacenS3`) y el frontend las recibe por URL firmada, no a través del backend.
- **Rendimiento:** exportar los pesos a ONNX/OpenVINO para CPU (`yolo export format=onnx`) como `DetectorOnnx` sin tocar casos de uso.

---

## D. Preparación para despliegue

### D.1 Dockerfile backend (multi-stage, producción)

```dockerfile
# backend/Dockerfile
# syntax=docker/dockerfile:1.7

############################
# Etapa 1: dependencias
############################
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Capa cacheable: solo cambia si cambian las dependencias
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Código de la app (instalado como paquete, no editable)
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

############################
# Etapa 2: runtime mínimo
############################
FROM python:3.12-slim AS runtime

# Librerías de sistema que necesitan OpenCV/Ultralytics
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --create-home app

WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app models ./models

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    YOLO_CONFIG_DIR=/tmp/ultralytics \
    APP_ENV=prod \
    FORWARDED_ALLOW_IPS=127.0.0.1

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=3)"

# 1 worker por contenedor (modelos en memoria); escalar con réplicas.
# FORWARDED_ALLOW_IPS: poner la IP/subred del proxy inverso. Nunca "*": cualquiera
# podría falsificar X-Forwarded-For y saltarse el rate limit por IP.
CMD ["uvicorn", "plagas.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--proxy-headers", "--no-server-header"]
```

En producción se ejecuta además con sistema de archivos de solo lectura (`read_only: true`, `tmpfs: /tmp`), `cap_drop: [ALL]` y `no-new-privileges` (ver §E.5).

Para no meter CUDA (~2 GB extra) en una imagen que corre en CPU, `pyproject.toml` fija torch a la rueda CPU:

```toml
[project]
name = "plagas"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115", "uvicorn[standard]>=0.32", "pydantic-settings>=2.6",
  "python-multipart>=0.0.12", "sqlalchemy[asyncio]>=2.0", "asyncpg>=0.30",
  "alembic>=1.14", "structlog>=24.4", "ultralytics>=8.3", "torch>=2.5", "pillow>=11",
  "anyio>=4.6",
]

[tool.uv.sources]
torch = { index = "pytorch-cpu" }
torchvision = { index = "pytorch-cpu" }

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

Las migraciones se ejecutan como **paso separado** del despliegue (job / init container), no al arrancar cada réplica:

```bash
docker run --rm --env-file .env.prod plagas-backend alembic upgrade head
```

### D.2 Dockerfile frontend (multi-stage + Nginx)

La URL de la API **no se hornea en el build**: se inyecta al arrancar el contenedor mediante `config.js`. Así **la misma imagen** se promueve de staging a prod.

```dockerfile
# frontend/Dockerfile
# syntax=docker/dockerfile:1.7

############################
# Etapa 1: build
############################
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

COPY . .
RUN npm run build          # tsc -b && vite build  -> /app/dist

############################
# Etapa 2: servir estáticos
############################
FROM nginx:1.27-alpine AS runtime

# La imagen oficial aplica envsubst a /etc/nginx/templates/*.template al arrancar
# (solo sustituye variables definidas, así que $uri y similares se conservan)
COPY nginx/default.conf.template nginx/seguridad.inc.template /etc/nginx/templates/
COPY nginx/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh
COPY --from=build /app/dist /usr/share/nginx/html

RUN chmod +x /docker-entrypoint.d/40-runtime-config.sh

ENV API_BASE_URL=http://localhost:8000 \
    AUTH_URL=http://localhost:8081 \
    IMAGENES_URL=http://localhost:8000 \
    APP_ENV=prod

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1/healthz || exit 1
# CMD heredado de nginx: los scripts de /docker-entrypoint.d se ejecutan antes de arrancar
```

```sh
# frontend/nginx/40-runtime-config.sh
#!/bin/sh
set -eu
envsubst '${API_BASE_URL} ${AUTH_URL} ${APP_ENV}' \
  < /usr/share/nginx/html/config.js.template \
  > /usr/share/nginx/html/config.js
```

```js
// frontend/public/config.js.template
window.__APP_CONFIG__ = {
  apiBaseUrl: "${API_BASE_URL}",
  authUrl: "${AUTH_URL}",
  env: "${APP_ENV}",
};
```

```nginx
# frontend/nginx/default.conf.template  (cabeceras de seguridad completas en §E.5)
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    server_tokens off;

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;

    # Cada location con add_header propio debe repetir el include (§E.5)
    include /etc/nginx/conf.d/seguridad.inc;

    # Assets con hash de Vite: caché agresiva
    location /assets/ {
        include /etc/nginx/conf.d/seguridad.inc;
        add_header Cache-Control "public, immutable";
        expires 1y;
    }

    # Configuración de runtime y el HTML nunca se cachean
    location = /config.js {
        include /etc/nginx/conf.d/seguridad.inc;
        add_header Cache-Control "no-store";
    }
    location = /index.html {
        include /etc/nginx/conf.d/seguridad.inc;
        add_header Cache-Control "no-cache";
    }

    location = /healthz { access_log off; default_type text/plain; return 200 "ok"; }

    # SPA: cualquier ruta del router de React cae en index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```html
<!-- frontend/index.html: cargar config.js ANTES del bundle -->
<script src="/config.js"></script>
<script type="module" src="/src/main.tsx"></script>
```

### D.3 Variables de entorno por ambiente

**Frontend** — un solo punto de lectura, validado con Zod:

```ts
// core/config/env.ts
import { z } from 'zod';

declare global {
  interface Window { __APP_CONFIG__?: Partial<Record<'apiBaseUrl' | 'authUrl' | 'env', string>> }
}

const EnvSchema = z.object({
  apiBaseUrl: z.string().url(),
  authUrl: z.string().url(),
  env: z.enum(['dev', 'staging', 'prod']),
});

// Prioridad: config.js de runtime (contenedor) > variables de Vite (desarrollo local)
export const env = EnvSchema.parse({
  apiBaseUrl: window.__APP_CONFIG__?.apiBaseUrl ?? import.meta.env.VITE_API_BASE_URL,
  authUrl: window.__APP_CONFIG__?.authUrl ?? import.meta.env.VITE_AUTH_URL,
  env: window.__APP_CONFIG__?.env ?? import.meta.env.VITE_APP_ENV ?? 'dev',
});
```

En desarrollo local, `public/config.js` (git-ignored) puede no existir; entonces se usan los `VITE_*`:

```bash
# frontend/.env.example  (copiar a .env.development.local)
VITE_API_BASE_URL=http://localhost:8000
VITE_AUTH_URL=http://localhost:8081/realms/plagas
VITE_APP_ENV=dev
```

**Backend:**

```bash
# backend/.env.example
APP_ENV=dev
APP_LOG_LEVEL=DEBUG
APP_DATABASE_URL=postgresql+asyncpg://plagas:plagas@db:5432/plagas
APP_CORS_ORIGINS=["http://localhost:5173","http://localhost:8080"]
APP_MODELOS_DIR=models
APP_MODELO_HOJAS=hojas.pt
APP_MODELO_FRUTOS=frutos.pt
APP_YOLO_IMGSZ=1024
APP_UMBRAL_CONFIANZA=0.35
APP_ALMACEN=local
APP_ALMACEN_LOCAL_DIR=/data/imagenes
# APP_S3_BUCKET=plagas-imagenes-staging

# Seguridad (§E)
APP_OIDC_EMISOR=http://localhost:8081/realms/plagas
APP_OIDC_AUDIENCIA=api-plagas
APP_OIDC_JWKS_URL=http://keycloak:8080/realms/plagas/protocol/openid-connect/certs
APP_HOSTS_PERMITIDOS=["localhost","127.0.0.1","backend"]
APP_RATE_LIMIT_STORAGE=memory://
APP_SHA256_MODELO_HOJAS=<sha256 de models/hojas.pt>
APP_SHA256_MODELO_FRUTOS=<sha256 de models/frutos.pt>
```

**Matriz por ambiente:**

| Variable | dev | staging | prod |
|---|---|---|---|
| `API_BASE_URL` (front) | `http://localhost:8000` | `https://api.staging.plagas-palta.app` | `https://api.plagas-palta.app` |
| `APP_ENV` | `dev` | `staging` | `prod` |
| `APP_CORS_ORIGINS` | `["http://localhost:5173"]` | `["https://staging.plagas-palta.app"]` | `["https://plagas-palta.app"]` |
| `APP_DATABASE_URL` | Postgres de compose | Postgres gestionado (secreto) | Postgres gestionado (secreto) |
| `APP_ALMACEN` | `local` | `s3` | `s3` |
| `APP_LOG_LEVEL` | `DEBUG` | `INFO` | `INFO` |
| `/docs` (Swagger) | visible | visible | oculto |

Los secretos (URL de BD, credenciales S3) **nunca** van en archivos versionados: se inyectan desde el gestor de secretos de la plataforma (GitHub Environments, Docker secrets, etc.).

### D.4 Orquestación local

```yaml
# docker-compose.yml
name: plagas-palta

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: plagas
      POSTGRES_PASSWORD: plagas
      POSTGRES_DB: plagas
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U plagas"]
      interval: 5s
      retries: 10

  backend:
    build: ./backend
    env_file: ./backend/.env
    depends_on:
      db: { condition: service_healthy }
    ports: ["8000:8000"]
    volumes:
      - imagenes:/data/imagenes
      - ./backend/models:/app/models:ro      # cambiar pesos sin reconstruir la imagen

  frontend:
    build: ./frontend
    environment:
      API_BASE_URL: http://localhost:8000
      APP_ENV: dev
    depends_on: [backend]
    ports: ["8080:80"]

volumes:
  pgdata:
  imagenes:
```

```yaml
# docker-compose.override.yml  (solo desarrollo: hot reload)
services:
  backend:
    command: uvicorn plagas.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend/src:/app/src
```

```makefile
# Makefile
.PHONY: up lint test gen-api

up:        ; docker compose up --build
lint:      ; cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run lint-imports
	cd frontend && npm run lint && npm run typecheck
test:      ; cd backend && uv run pytest && cd ../frontend && npm test
gen-api:   ; cd backend && uv run python -m plagas.scripts.exportar_openapi > ../openapi.json
	cd frontend && npm run gen:api
```

**Pesos del modelo:** los `.pt` no se suben a git. Opciones, de menor a mayor madurez:
1. Volumen montado (`./backend/models`) — desarrollo.
2. Descarga en el pipeline de CI desde un *release* de GitHub o un bucket antes de `docker build` — staging/prod.
3. Registro de modelos (MLflow / W&B) con `manifest.json` que fija la versión desplegada; el endpoint `/health/ready` expone la versión cargada.

### D.5 Pipeline de CI (resumen)

1. **Secretos:** `gitleaks` sobre el diff.
2. **Backend:** `ruff` (incluye reglas `S` de seguridad, equivalentes a Bandit) → `mypy --strict` → `lint-imports` → `pip-audit` → `pytest` unit + contract + api con cobertura → `pytest -m integration` (testcontainers).
3. **Frontend:** `eslint` (incluye boundaries) → `tsc --noEmit` → `npm audit --omit=dev --audit-level=high` → `vitest --coverage`.
4. **Contrato:** exportar OpenAPI y verificar que no hay diff con `openapi.json`; `npm run check:api`.
5. **Modelo** (solo si cambian los pesos o `manifest.json`): `pytest -m modelo` con el golden set.
6. **Imágenes:** build de ambos Dockerfiles, escaneo con Trivy (falla con CVEs `HIGH`/`CRITICAL` corregibles), push con tag = SHA del commit.
7. **Deploy:** staging automático desde `dev` + smoke test E2E con Playwright; prod desde `main` con aprobación manual, reutilizando la misma imagen.

Detalle de seguridad en §E y de pruebas en §F.

---

## E. Seguridad

> **Supuesto:** la app tiene usuarios con cuenta (agricultores y técnicos agrónomos) y cada uno ve solo su historial. Si se decide que sea **anónima**, se eliminan §E.3 y el campo `propietario_id`; el resto de la sección se mantiene igual.

### E.1 Modelo de amenazas

| Activo | Amenaza | Control | Sección |
|---|---|---|---|
| Servidor de inferencia | Archivo malicioso (polyglot, bomba de descompresión, imagen corrupta que tumba Pillow) | Magic bytes + límite de píxeles + re-codificación | E.2 |
| Servidor de inferencia | DoS por subidas enormes o muchas peticiones | Límite de cuerpo en proxy y app, rate limiting, 1 inferencia a la vez por réplica | E.2, E.4 |
| Historial de diagnósticos | Un usuario lee diagnósticos ajenos adivinando IDs (IDOR) | JWT + control de propiedad en el caso de uso, 404 en vez de 403 | E.3 |
| Fotos del agricultor | Fuga de ubicación GPS por EXIF; bucket público | Re-codificación sin EXIF, bucket privado, URLs firmadas cortas | E.2, E.6 |
| Pesos `.pt` | Pickle manipulado = ejecución remota de código al cargar | Verificación SHA-256 antes de cargar | E.7 |
| Frontend | XSS, clickjacking, robo de token | CSP estricta, `frame-ancestors 'none'`, token solo en memoria | E.3, E.5 |
| Dependencias e imágenes | CVEs conocidos, secretos en git | pip-audit, npm audit, Trivy, gitleaks, Dependabot | E.8 |
| Logs | Tokens o datos personales en logs | Redacción automática en structlog | E.9 |

### E.2 Validación robusta de imágenes

El `content_type` que manda el cliente **no es confiable**. Hay tres barreras, de afuera hacia adentro:

1. **Proxy / Nginx de ingreso:** `client_max_body_size 12m` corta antes de llegar a Python.
2. **`LimiteCuerpoMiddleware`:** FastAPI parsea el multipart completo *antes* de llamar al endpoint, así que validar en el router llega tarde. El middleware rechaza con 413 si `Content-Length` supera el máximo y con 411 si falta (sin `Transfer-Encoding: chunked` en endpoints de subida).
3. **`InspectorImagenesPillow`** (adapter del puerto `InspectorImagenes`): verifica la firma binaria, limita los píxeles, decodifica la imagen por completo y la **re-codifica a JPEG**, lo que elimina EXIF/GPS y cualquier carga útil oculta.

```python
# shared/api/seguridad.py (parte 1)
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

METODOS_CON_CUERPO = {b"POST", b"PUT", b"PATCH"}


class LimiteCuerpoMiddleware:
    """Middleware ASGI puro: no carga el cuerpo, solo inspecciona cabeceras."""

    def __init__(self, app: ASGIApp, maximo_bytes: int) -> None:
        self.app = app
        self.maximo = maximo_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"].encode() in METODOS_CON_CUERPO:
            cabeceras = dict(scope["headers"])
            longitud = cabeceras.get(b"content-length")
            if longitud is None:
                return await self._rechazar(scope, receive, send, 411, "longitud_requerida")
            if not longitud.isdigit() or int(longitud) > self.maximo:
                return await self._rechazar(scope, receive, send, 413, "cuerpo_demasiado_grande")
        await self.app(scope, receive, send)

    async def _rechazar(self, scope, receive, send, status: int, codigo: str) -> None:
        respuesta = JSONResponse(
            {"type": f"https://plagas-palta.app/errores/{codigo}", "title": codigo, "status": status},
            status_code=status, media_type="application/problem+json",
        )
        await respuesta(scope, receive, send)
```

```python
# modules/diagnostico/infrastructure/inspector_pillow.py
import io

import anyio
from PIL import Image as PILImage
from PIL import ImageOps, UnidentifiedImageError

from ..domain.errors import ImagenInvalida
from ..domain.value_objects import Imagen

MAX_PIXELES = 40_000_000          # ~6300x6300; una foto de celular de 48 MP se reduce antes en el frontend
LADO_MINIMO = 224                 # por debajo el modelo no tiene detalle suficiente
LADO_MAXIMO_SALIDA = 2048         # el modelo trabaja a 1024; no tiene sentido guardar más

PILImage.MAX_IMAGE_PIXELS = MAX_PIXELES   # Pillow lanza DecompressionBombError por encima de 2x


def detectar_mime(datos: bytes) -> str | None:
    if datos.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if datos.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if datos[:4] == b"RIFF" and datos[8:12] == b"WEBP":
        return "image/webp"
    return None


class InspectorImagenesPillow:
    """Cumple InspectorImagenes. Toda falla de Pillow se traduce a ImagenInvalida (LSP)."""

    async def sanear(self, imagen: Imagen) -> Imagen:
        return await anyio.to_thread.run_sync(self._sanear, imagen)

    def _sanear(self, imagen: Imagen) -> Imagen:
        mime_real = detectar_mime(imagen.contenido)
        if mime_real is None or mime_real != imagen.tipo_mime:
            raise ImagenInvalida("El contenido no corresponde a una imagen JPEG, PNG o WebP")

        try:
            with PILImage.open(io.BytesIO(imagen.contenido)) as img:
                # open() es perezoso: el tamaño sale de la cabecera sin decodificar píxeles
                if img.width * img.height > MAX_PIXELES:
                    raise ImagenInvalida("La imagen tiene demasiados píxeles")
                if min(img.width, img.height) < LADO_MINIMO:
                    raise ImagenInvalida(f"La imagen debe medir al menos {LADO_MINIMO}px por lado")
                img.verify()                                   # detecta archivos truncados/corruptos

            with PILImage.open(io.BytesIO(imagen.contenido)) as img:
                limpia = ImageOps.exif_transpose(img).convert("RGB")   # respeta la rotación del celular
                limpia.thumbnail((LADO_MAXIMO_SALIDA, LADO_MAXIMO_SALIDA))
                salida = io.BytesIO()
                limpia.save(salida, format="JPEG", quality=90)          # sin exif= -> sin metadatos
        except ImagenInvalida:
            raise
        except (PILImage.DecompressionBombError, UnidentifiedImageError, OSError, SyntaxError, ValueError) as e:
            raise ImagenInvalida("La imagen está dañada o no es válida") from e

        return Imagen(contenido=salida.getvalue(), tipo_mime="image/jpeg")
```

> El frontend además **redimensiona en el cliente** a 2048 px antes de subir (canvas + `toBlob('image/jpeg', 0.9)`): menos datos móviles para el agricultor en campo y menos carga en el servidor. Esto es una optimización, no un control de seguridad; el servidor valida siempre.

### E.3 Autenticación y autorización

**Decisión:** no implementar login propio (hash de contraseñas, recuperación, MFA). Se delega en un proveedor **OIDC** (Keycloak autoalojado, Auth0, Cognito, Firebase Auth o Supabase Auth). El backend solo **verifica** JWT firmados con las claves públicas del proveedor (JWKS). Cambiar de proveedor = cambiar un adapter (DIP).

**Roles** (claim `roles` del token):

| Rol | Puede |
|---|---|
| `agricultor` | Crear diagnósticos, ver y borrar los suyos |
| `tecnico` | Lo anterior + ver los diagnósticos de todos (asistencia técnica) |
| `admin` | Lo anterior + gestionar el catálogo de enfermedades |

```python
# shared/domain/identidad.py
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Usuario:
    id: str                          # claim "sub" del proveedor
    roles: frozenset[str]

    @property
    def puede_ver_todo(self) -> bool:
        return bool({"tecnico", "admin"} & self.roles)

    @property
    def es_admin(self) -> bool:
        return "admin" in self.roles
```

```python
# shared/infrastructure/oidc.py
import jwt
from jwt import PyJWKClient

from ..domain.errors import NoAutenticado
from ..domain.identidad import Usuario


class VerificadorJwtOidc:
    """Cumple VerificadorTokens. Las claves JWKS se cachean; solo se descargan al rotar."""

    def __init__(self, emisor: str, audiencia: str, jwks_url: str) -> None:
        self._emisor = emisor
        self._audiencia = audiencia
        self._jwks = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)

    def verificar(self, token: str) -> Usuario:
        try:
            clave = self._jwks.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                clave,
                algorithms=["RS256", "ES256"],      # lista fija: nunca "none" ni HS* con clave pública
                audience=self._audiencia,
                issuer=self._emisor,
                options={"require": ["exp", "iat", "sub", "iss", "aud"]},
                leeway=30,
            )
        except jwt.PyJWTError as e:
            raise NoAutenticado("Token inválido o expirado") from e
        return Usuario(id=claims["sub"], roles=frozenset(claims.get("roles", [])))
```

```python
# shared/api/dependencias.py
from fastapi import Request


def get_container(request: Request):
    return request.app.state.container
```

```python
# shared/api/auth.py
from typing import Annotated

import anyio
import structlog
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..domain.errors import NoAutenticado
from ..domain.identidad import Usuario
from .dependencias import get_container

_bearer = HTTPBearer(auto_error=False)    # el error lo damos nosotros, en formato problem+json


async def get_usuario_actual(
    request: Request,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    container=Depends(get_container),
) -> Usuario:
    if credenciales is None:
        raise NoAutenticado("Falta el token de acceso")
    # verificar() puede descargar el JWKS (I/O bloqueante): fuera del event loop
    usuario = await anyio.to_thread.run_sync(container.verificador_tokens.verificar, credenciales.credentials)
    request.state.usuario = usuario                                  # lo usa el rate limiter
    structlog.contextvars.bind_contextvars(usuario_id=usuario.id)   # trazabilidad en logs
    return usuario
```

> `get_container` vive en `shared/api/` porque lo usan todos los módulos; `modules/*/api/dependencies.py` lo importan de ahí en lugar de definir el suyo.

**Autorización en el caso de uso, no en el router.** La regla "solo el dueño o un técnico" es de negocio y se prueba sin HTTP. Se responde **404** (no 403) para no revelar qué IDs existen:

```python
# modules/diagnostico/application/use_cases/obtener_diagnostico.py
from uuid import UUID

from ....shared.domain.identidad import Usuario
from ...domain.errors import DiagnosticoNoEncontrado
from ..dtos import DiagnosticoDTO
from ..ports import LecturaDiagnosticos


class ObtenerDiagnostico:
    def __init__(self, lectura: LecturaDiagnosticos) -> None:
        self._lectura = lectura

    async def ejecutar(self, id: UUID, usuario: Usuario) -> DiagnosticoDTO:
        diagnostico = await self._lectura.por_id(id)
        if diagnostico is None or not diagnostico.visible_para(usuario):
            raise DiagnosticoNoEncontrado(f"No existe el diagnóstico {id}")
        return DiagnosticoDTO.desde_entidad(diagnostico)
```

`ListarHistorial` filtra por `propietario_id` en la consulta SQL (salvo `puede_ver_todo`); nunca trae todo y filtra en Python.

**Frontend:**
- Flujo **Authorization Code + PKCE** con `oidc-client-ts` (nunca el flujo implícito).
- El access token vive **solo en memoria** (no `localStorage`, que es accesible a cualquier XSS). La sesión se renueva en silencio con el refresh token rotativo del proveedor.
- `core/http/client.ts` añade el token con un middleware; ninguna feature toca el token.

```ts
// core/http/client.ts (añadido)
import { obtenerToken } from '../auth/sesion';

const autenticacion: Middleware = {
  async onRequest({ request }) {
    const token = await obtenerToken();          // renueva si está por expirar
    if (token) request.headers.set('Authorization', `Bearer ${token}`);
    return request;
  },
};

apiClient.use(autenticacion);
apiClient.use(errores);
```

- Ante un `401`, `QueryCache.onError` redirige al login; ante `403`, muestra "sin permiso".
- **Ojo:** ocultar botones según el rol es solo UX. La autorización real está siempre en el backend.

**Desarrollo local:** se añade un Keycloak a `docker-compose.yml` con un realm `plagas` importado desde `infra/keycloak/realm-plagas.json` (usuarios de prueba `agricultor1`, `tecnico1`).

### E.4 Rate limiting y protección de la inferencia

| Capa | Límite | Para qué |
|---|---|---|
| Proxy de ingreso (Nginx/Traefik/LB) | `limit_req` ~30 r/s por IP con ráfaga | Frenar floods antes de Python |
| App (`slowapi`) | `POST /diagnosticos`: 10/min por **usuario**; resto: 120/min | Costo de inferencia por cuenta |
| `DetectorYolo` | `threading.Lock`: 1 inferencia simultánea por réplica | Memoria/CPU acotadas; el resto espera en cola |

```python
# shared/api/seguridad.py (parte 2)
import os

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request

from .errors import _problema


def clave_limite(request: Request) -> str:
    # slowapi evalúa el límite después de resolver las dependencias del endpoint, así que
    # get_usuario_actual ya verificó el JWT y dejó el usuario en request.state.
    # Sin usuario: IP real (requiere FORWARDED_ALLOW_IPS correcto).
    usuario = getattr(request.state, "usuario", None)
    return f"u:{usuario.id}" if usuario else f"ip:{get_remote_address(request)}"


# El limiter se crea al importar (lo necesitan los decoradores de los routers),
# por eso lee el storage directamente del entorno: memory:// en dev, redis:// con réplicas.
limiter = Limiter(
    key_func=clave_limite,
    default_limits=["120/minute"],
    storage_uri=os.getenv("APP_RATE_LIMIT_STORAGE", "memory://"),
)


def configurar_rate_limit(app) -> None:
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def _excedido(request: Request, exc: RateLimitExceeded):
        return _problema(429, "limite_excedido", "Demasiadas solicitudes, intenta en un minuto", request)
```

> Con `memory://` cada réplica cuenta por separado; con más de una réplica es **obligatorio** `redis://` para que el límite sea global.

### E.5 Cabeceras HTTP, TLS y endurecimiento de contenedores

**TLS:** se termina en el proxy de ingreso (Caddy/Traefik con Let's Encrypt, o el balanceador de la nube). Todo el tráfico externo es HTTPS; HTTP solo redirige con 301. Entre proxy y contenedores hay una red interna.

**Frontend** — `frontend/nginx/seguridad.inc.template`. Se copia a `/etc/nginx/templates/` y la imagen oficial de Nginx genera `/etc/nginx/conf.d/seguridad.inc` con las URLs reales en la CSP. Como no termina en `.conf`, solo se carga donde se hace `include`:

```nginx
# Content-Security-Policy: solo nuestro origen, la API, el almacén de imágenes y el proveedor de identidad
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data: ${API_BASE_URL} ${IMAGENES_URL}; connect-src 'self' ${API_BASE_URL} ${AUTH_URL}; frame-src ${AUTH_URL}; frame-ancestors 'none'; base-uri 'self'; form-action 'self' ${AUTH_URL}; object-src 'none'" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(self), geolocation=(), microphone=(), payment=()" always;
add_header Cross-Origin-Opener-Policy "same-origin" always;
```

> **Trampa de Nginx:** un `location` que tiene su propio `add_header` (como `/assets/` o `/config.js`) **descarta** los `add_header` del nivel `server`. Por eso `seguridad.inc` se incluye dentro de cada `location` (ver §D.2), no solo una vez en `server`.
>
> `IMAGENES_URL` es el origen de las URLs firmadas del bucket (p. ej. `https://plagas-imagenes.s3.amazonaws.com`).
>
> `camera=(self)` permite usar la cámara del celular desde la propia app para tomar la foto. `'unsafe-inline'` en estilos solo si la librería de UI lo requiere; si no, quitarlo.

**Backend** — las respuestas de la API contienen datos personales, así que no deben cachearse:

```python
# shared/api/seguridad.py (parte 3)
from starlette.middleware.base import BaseHTTPMiddleware


class CabecerasSeguridadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        return response
```

**Contenedores** (en el compose/manifiesto de producción):

```yaml
services:
  backend:
    read_only: true
    tmpfs: [/tmp]
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    deploy:
      resources:
        limits: { cpus: "2", memory: 3g }   # una imagen maliciosa no tumba el host
  frontend:
    cap_drop: [ALL]
    cap_add: [CHOWN, SETGID, SETUID, NET_BIND_SERVICE]   # requeridos por nginx al arrancar
    security_opt: ["no-new-privileges:true"]
```

Además: imágenes base fijadas por *digest* (`python:3.12-slim@sha256:...`), actualizadas por Dependabot.

### E.6 Almacenamiento de imágenes y privacidad

- **Nombres:** la clave del objeto es `diagnosticos/{yyyy}/{mm}/{uuid4}.jpg`. Nunca se usa el nombre de archivo del cliente (evita *path traversal* y fuga de datos en el nombre).
- **Bucket privado**, cifrado en reposo (SSE), sin listado público. El frontend recibe **URLs firmadas** de 15 minutos generadas por `AlmacenImagenes.url_publica`.
- **EXIF/GPS eliminado** en la re-codificación (§E.2). Si en el futuro se quiere el mapa de brotes por zona, la ubicación se pide **explícitamente** al usuario y se guarda redondeada (p. ej. a nivel de distrito), no se extrae a escondidas de la foto.
- **Retención:** un job diario borra imágenes y diagnósticos más antiguos que `APP_RETENCION_DIAS` (por defecto 365).
- **Derecho de supresión:** `DELETE /api/v1/diagnosticos/{id}` (dueño) y `DELETE /api/v1/usuarios/yo/datos` (borra todo el historial del usuario). Esto alinea la app con la Ley N.º 29733 de Protección de Datos Personales (Perú) y normas similares.
- **Uso para reentrenar:** si se quieren usar las fotos para mejorar el modelo, se pide **consentimiento explícito** (casilla no marcada por defecto) y se guarda en el diagnóstico (`consentimiento_entrenamiento: bool`).

### E.7 Integridad de los pesos del modelo

`YOLO("x.pt")` usa `torch.load`, que deserializa **pickle**: un `.pt` manipulado ejecuta código arbitrario al cargarse. Por eso:

1. `manifest.json` registra el SHA-256 de cada peso al promoverlo desde `ml/`.
2. El hash esperado llega por variable de entorno (`APP_SHA256_MODELO_*`), separada del archivo.
3. El container verifica el hash **antes** de cargar; si no coincide, la app no arranca.

```python
# shared/infrastructure/integridad.py
import hashlib
import hmac
from pathlib import Path


class PesosAlterados(RuntimeError):
    pass


def verificar_sha256(ruta: Path, esperado: str) -> None:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    if not hmac.compare_digest(h.hexdigest(), esperado.lower()):
        raise PesosAlterados(f"El hash de {ruta.name} no coincide con el esperado")
```

> Mejora a futuro: exportar a **ONNX** (`yolo export format=onnx`) y servir con `DetectorOnnx`. ONNX no usa pickle, así que desaparece este vector de ataque, y además la inferencia en CPU es más rápida.

### E.8 Cadena de suministro y secretos

| Herramienta | Dónde | Qué detecta |
|---|---|---|
| `gitleaks` | pre-commit + CI | Claves y tokens commiteados |
| `ruff` reglas `S` (flake8-bandit) | pre-commit + CI | `eval`, `subprocess` con shell, `assert` como control, hashes débiles, etc. |
| `pip-audit` | CI | CVEs en dependencias Python (`uv export --no-dev \| pip-audit -r /dev/stdin`) |
| `npm audit --omit=dev` | CI | CVEs en dependencias de producción del frontend |
| Dependabot | GitHub | PRs semanales para pip, npm, Docker y GitHub Actions |
| Trivy | CI, sobre la imagen final | CVEs del sistema operativo y librerías dentro del contenedor |

- `uv.lock` y `package-lock.json` versionados; las instalaciones usan `--frozen` / `npm ci`.
- Las GitHub Actions se fijan por SHA, no por tag.
- Secretos solo en GitHub Environments / gestor de secretos del proveedor; `.env` está en `.gitignore` y solo se versionan los `.env.example`.

### E.9 Logs y errores sin fugas

- Los errores 500 devuelven un mensaje genérico + `request_id`; la traza completa va solo al log (§C.2).
- Procesador de structlog que **redacta** campos sensibles antes de serializar:

```python
# shared/infrastructure/logging.py (extracto)
CAMPOS_SENSIBLES = {"authorization", "token", "access_token", "password", "cookie", "contenido"}


def redactar(_, __, evento: dict) -> dict:
    for clave in list(evento):
        if clave.lower() in CAMPOS_SENSIBLES:
            evento[clave] = "[REDACTADO]"
    return evento
```

- Se registran eventos de seguridad con nivel `warning`: tokens inválidos (sin el token), 429, imágenes rechazadas (con el motivo, sin el contenido) y accesos 404 a diagnósticos ajenos (posible enumeración).

### E.10 Checklist de seguridad antes de pasar a producción

- [ ] HTTPS con HSTS; HTTP solo redirige.
- [ ] `APP_CORS_ORIGINS` y `APP_HOSTS_PERMITIDOS` con dominios exactos (sin `*`).
- [ ] `FORWARDED_ALLOW_IPS` = IP/subred del proxy.
- [ ] `/docs` y `/openapi.json` deshabilitados en prod.
- [ ] Rate limiting con Redis si hay más de una réplica.
- [ ] Hash SHA-256 de los pesos configurado y verificado al arrancar.
- [ ] Bucket privado, cifrado, con URLs firmadas.
- [ ] Job de retención activo; endpoints de borrado probados.
- [ ] Contenedores con usuario no root, `read_only`, `cap_drop: ALL` y límites de memoria.
- [ ] CI en verde: gitleaks, pip-audit, npm audit, Trivy sin `HIGH`/`CRITICAL` corregibles.
- [ ] Tests de seguridad de §F.6 pasando (401, 404 para ajenos, 413, 422 por magic bytes, 429).

---

## F. Estrategia de pruebas

### F.1 Pirámide y herramientas

```
                ▲  E2E (Playwright)            pocos, lentos: 1-3 flujos críticos en staging
               ▲▲  API (httpx + ASGITransport)  contrato HTTP, auth, errores, límites
              ▲▲▲  Integración / contrato       Postgres real, Pillow real, YOLO real (marcados)
            ▲▲▲▲▲  Unitarias                    dominio + casos de uso con fakes: la mayoría, < 1 s total
```

| Nivel | Backend | Frontend | ¿Corre en cada PR? |
|---|---|---|---|
| Unitarias | `pytest`, `pytest-asyncio` | `vitest` | Sí |
| Contrato (LSP) | Suite compartida fake vs. real | — | Sí (fake) / Sí con Docker (real) |
| Integración | `testcontainers[postgres]` | `vitest` + MSW | Sí |
| Componentes | — | Testing Library + `user-event` | Sí |
| API | `httpx.AsyncClient` + `ASGITransport` | — | Sí |
| Regresión del modelo | `pytest -m modelo` + golden set | — | Solo si cambian los pesos |
| E2E | — | Playwright contra staging | Tras desplegar a staging |

**Objetivos de cobertura** (con *branch coverage*): `domain/` y `application/` ≥ 90 %; total del backend ≥ 80 %; frontend `features/*/model`, `hooks` y `core/` ≥ 80 %. La cobertura es una alarma, no una meta: un test sin aserciones relevantes no cuenta.

**Reglas:**
- Las unitarias **no** tocan red, disco, BD, reloj real ni YOLO.
- Un test = un comportamiento; nombre en español que describe la regla (`test_diagnostico_con_solo_clases_sanas_es_sano`).
- Estructura *Arrange / Act / Assert*.
- Cada bug corregido trae su test de regresión.

### F.2 Configuración

```toml
# backend/pyproject.toml
[dependency-groups]
dev = [
  "pytest>=8.3", "pytest-asyncio>=0.24", "pytest-cov>=6.0", "httpx>=0.28",
  "testcontainers[postgres]>=4.8", "mypy>=1.13", "ruff>=0.8", "import-linter>=2.1",
  "pip-audit>=2.7",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
markers = [
  "integration: requiere Docker (Postgres con testcontainers)",
  "modelo: requiere los pesos reales en models/",
]
# Por defecto: rápidas. CI ejecuta luego `pytest -m integration` y, si aplica, `pytest -m modelo`.
addopts = "-m 'not integration and not modelo' --strict-markers --cov=plagas --cov-branch --cov-report=term-missing"

[tool.coverage.report]
fail_under = 80
exclude_also = ["if TYPE_CHECKING:", "raise NotImplementedError", "\\.\\.\\."]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "S", "ASYNC", "PT", "SIM", "RUF"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]          # assert está bien en tests
```

### F.3 Dobles de prueba y fábricas

Un fake por puerto, en un solo archivo. Son implementaciones **reales y simples** (no mocks con `MagicMock`): pasan la misma suite de contrato que los adapters (§F.5), así que no mienten sobre el comportamiento.

```python
# tests/fakes.py
from datetime import UTC, datetime
from uuid import UUID

from plagas.modules.diagnostico.domain.entities import Diagnostico
from plagas.modules.diagnostico.domain.errors import ImagenInvalida, OrganoNoSoportado
from plagas.modules.diagnostico.domain.value_objects import Deteccion, Imagen, Organo
from plagas.shared.domain.errors import NoAutenticado
from plagas.shared.domain.identidad import Usuario


class DetectorFalso:
    def __init__(self, detecciones: list[Deteccion] | None = None) -> None:
        self.detecciones = detecciones or []
        self.recibidas: list[Imagen] = []

    async def detectar(self, imagen: Imagen) -> list[Deteccion]:
        self.recibidas.append(imagen)
        return list(self.detecciones)


class ProveedorDetectoresFalso:
    def __init__(self, detectores: dict[Organo, DetectorFalso]) -> None:
        self._detectores = detectores

    def para(self, organo: Organo) -> DetectorFalso:
        if organo not in self._detectores:
            raise OrganoNoSoportado(f"Sin modelo para {organo}")
        return self._detectores[organo]


class InspectorQueAcepta:
    async def sanear(self, imagen: Imagen) -> Imagen:
        return imagen


class InspectorQueRechaza:
    async def sanear(self, imagen: Imagen) -> Imagen:
        raise ImagenInvalida("rechazada por el inspector")


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}

    async def guardar(self, imagen: Imagen) -> str:
        ref = f"mem/{len(self.objetos)}.jpg"
        self.objetos[ref] = imagen.contenido
        return ref

    async def url_publica(self, referencia: str) -> str:
        return f"https://almacen.test/{referencia}"


class RepoEnMemoria:
    """Cumple EscrituraDiagnosticos y LecturaDiagnosticos."""

    def __init__(self) -> None:
        self.datos: dict[UUID, Diagnostico] = {}

    async def guardar(self, diagnostico: Diagnostico) -> None:
        self.datos[diagnostico.id] = diagnostico

    async def por_id(self, id: UUID) -> Diagnostico | None:
        return self.datos.get(id)

    async def recientes(self, limite: int, desplazamiento: int) -> list[Diagnostico]:
        ordenados = sorted(self.datos.values(), key=lambda d: d.creado_en, reverse=True)
        return ordenados[desplazamiento : desplazamiento + limite]


class RelojFijo:
    def __init__(self, momento: datetime = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)) -> None:
        self.momento = momento

    def ahora(self) -> datetime:
        return self.momento


class IdsSecuenciales:
    def __init__(self) -> None:
        self._n = 0

    def nuevo(self) -> UUID:
        self._n += 1
        return UUID(int=self._n)


class VerificadorFalso:
    def __init__(self, tokens: dict[str, Usuario]) -> None:
        self._tokens = tokens

    def verificar(self, token: str) -> Usuario:
        if token not in self._tokens:
            raise NoAutenticado("Token inválido o expirado")
        return self._tokens[token]
```

```python
# tests/factories.py
from plagas.modules.diagnostico.application.dtos import DiagnosticarImagenCommand
from plagas.modules.diagnostico.domain.value_objects import (
    CajaDelimitadora, Confianza, Deteccion, Organo,
)
from plagas.shared.domain.identidad import Usuario

JPEG_MINIMO = b"\xff\xd8\xff\xe0" + b"\x00" * 100        # suficiente para el value object

AGRICULTOR = Usuario(id="agricultor-1", roles=frozenset({"agricultor"}))
OTRO_AGRICULTOR = Usuario(id="agricultor-2", roles=frozenset({"agricultor"}))
TECNICO = Usuario(id="tecnico-1", roles=frozenset({"tecnico"}))


def deteccion(clase: str = "antracnosis_hoja", confianza: float = 0.9) -> Deteccion:
    return Deteccion(
        clase=clase,
        confianza=Confianza(confianza),
        caja=CajaDelimitadora(0.1, 0.1, 0.5, 0.5),
    )


def comando(
    organo: Organo = Organo.HOJA,
    propietario: Usuario = AGRICULTOR,
    contenido: bytes = JPEG_MINIMO,
    tipo_mime: str = "image/jpeg",
) -> DiagnosticarImagenCommand:
    return DiagnosticarImagenCommand(
        propietario_id=propietario.id, organo=organo, contenido=contenido, tipo_mime=tipo_mime,
    )
```

```python
# tests/conftest.py
import pytest

from plagas.modules.diagnostico.application.use_cases.diagnosticar_imagen import DiagnosticarImagen
from plagas.modules.diagnostico.domain.value_objects import Organo

from .fakes import (
    AlmacenEnMemoria, DetectorFalso, IdsSecuenciales, InspectorQueAcepta,
    ProveedorDetectoresFalso, RelojFijo, RepoEnMemoria,
)


@pytest.fixture
def repo() -> RepoEnMemoria:
    return RepoEnMemoria()


@pytest.fixture
def detector_hoja() -> DetectorFalso:
    return DetectorFalso()


@pytest.fixture
def detector_fruto() -> DetectorFalso:
    return DetectorFalso()


@pytest.fixture
def diagnosticar(repo, detector_hoja, detector_fruto) -> DiagnosticarImagen:
    return DiagnosticarImagen(
        inspector=InspectorQueAcepta(),
        detectores=ProveedorDetectoresFalso({Organo.HOJA: detector_hoja, Organo.FRUTO: detector_fruto}),
        almacen=AlmacenEnMemoria(),
        repositorio=repo,
        reloj=RelojFijo(),
        ids=IdsSecuenciales(),
        umbral_confianza=0.35,
    )
```

### F.4 Pruebas unitarias

**Dominio** (sin async, sin fixtures; corren en milisegundos):

```python
# tests/unit/diagnostico/test_dominio.py
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from plagas.modules.diagnostico.domain.entities import Diagnostico
from plagas.modules.diagnostico.domain.errors import ConfianzaInvalida, ImagenInvalida
from plagas.modules.diagnostico.domain.value_objects import (
    TAMANO_MAXIMO_BYTES, Confianza, Imagen, Organo,
)

from ...factories import AGRICULTOR, JPEG_MINIMO, OTRO_AGRICULTOR, TECNICO, deteccion


def registrar(detecciones, umbral=0.35, propietario=AGRICULTOR) -> Diagnostico:
    return Diagnostico.registrar(
        id=uuid4(), propietario_id=propietario.id, organo=Organo.HOJA, imagen_ref="x",
        detecciones=detecciones, umbral=umbral, ahora=datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestConfianza:
    @pytest.mark.parametrize("valor", [-0.01, 1.01, 5])
    def test_fuera_de_rango_es_invalida(self, valor):
        with pytest.raises(ConfianzaInvalida):
            Confianza(valor)

    @pytest.mark.parametrize("valor", [0.0, 0.5, 1.0])
    def test_limites_son_validos(self, valor):
        assert Confianza(valor).valor == valor


class TestImagen:
    @pytest.mark.parametrize("mime", ["image/gif", "application/pdf", "text/html", ""])
    def test_rechaza_formatos_no_soportados(self, mime):
        with pytest.raises(ImagenInvalida):
            Imagen(contenido=JPEG_MINIMO, tipo_mime=mime)

    def test_rechaza_imagen_vacia(self):
        with pytest.raises(ImagenInvalida):
            Imagen(contenido=b"", tipo_mime="image/jpeg")

    def test_rechaza_imagen_mayor_a_10_mb(self):
        with pytest.raises(ImagenInvalida):
            Imagen(contenido=b"\xff" * (TAMANO_MAXIMO_BYTES + 1), tipo_mime="image/jpeg")


class TestDiagnostico:
    def test_descarta_detecciones_bajo_el_umbral(self):
        d = registrar([deteccion("antracnosis_hoja", 0.20)], umbral=0.35)
        assert d.detecciones == ()
        assert d.es_sano

    def test_conserva_detecciones_en_el_umbral_exacto(self):
        d = registrar([deteccion("plaga", 0.35)], umbral=0.35)
        assert d.enfermedades == ["plaga"]

    def test_con_solo_clases_sanas_es_sano(self):
        d = registrar([deteccion("hoja_sana", 0.95), deteccion("hoja_sana", 0.80)])
        assert d.es_sano
        assert d.enfermedades == []

    def test_una_enfermedad_entre_sanas_lo_hace_enfermo(self):
        d = registrar([deteccion("hoja_sana", 0.9), deteccion("deficiencia_nutricional", 0.6)])
        assert not d.es_sano
        assert d.enfermedades == ["deficiencia_nutricional"]

    def test_enfermedades_sin_duplicados_y_ordenadas(self):
        d = registrar([deteccion("plaga"), deteccion("antracnosis_hoja"), deteccion("plaga")])
        assert d.enfermedades == ["antracnosis_hoja", "plaga"]

    def test_visible_para_el_dueno_y_para_tecnicos_pero_no_para_otros(self):
        d = registrar([], propietario=AGRICULTOR)
        assert d.visible_para(AGRICULTOR)
        assert d.visible_para(TECNICO)
        assert not d.visible_para(OTRO_AGRICULTOR)
```

**Casos de uso** (async, con fakes):

```python
# tests/unit/diagnostico/test_diagnosticar_imagen.py
import pytest

from plagas.modules.diagnostico.application.use_cases.diagnosticar_imagen import DiagnosticarImagen
from plagas.modules.diagnostico.domain.errors import ImagenInvalida, OrganoNoSoportado
from plagas.modules.diagnostico.domain.value_objects import Organo

from ...factories import AGRICULTOR, comando, deteccion
from ...fakes import (
    AlmacenEnMemoria, DetectorFalso, IdsSecuenciales, InspectorQueRechaza,
    ProveedorDetectoresFalso, RelojFijo, RepoEnMemoria,
)


async def test_guarda_el_diagnostico_y_devuelve_las_enfermedades(diagnosticar, detector_fruto, repo):
    detector_fruto.detecciones = [deteccion("cercospora", 0.8)]

    resultado = await diagnosticar.ejecutar(comando(organo=Organo.FRUTO))

    assert resultado.enfermedades == ["cercospora"]
    assert resultado.es_sano is False
    guardado = await repo.por_id(resultado.id)
    assert guardado is not None
    assert guardado.propietario_id == AGRICULTOR.id


async def test_usa_solo_el_detector_del_organo_pedido(diagnosticar, detector_hoja, detector_fruto):
    await diagnosticar.ejecutar(comando(organo=Organo.HOJA))

    assert len(detector_hoja.recibidas) == 1
    assert detector_fruto.recibidas == []


async def test_organo_sin_modelo_falla_sin_guardar_nada():
    repo = RepoEnMemoria()
    caso = DiagnosticarImagen(
        inspector=InspectorQueRechaza(),           # ni siquiera debe llegar a inspeccionar
        detectores=ProveedorDetectoresFalso({Organo.HOJA: DetectorFalso()}),
        almacen=AlmacenEnMemoria(), repositorio=repo,
        reloj=RelojFijo(), ids=IdsSecuenciales(), umbral_confianza=0.35,
    )

    with pytest.raises(OrganoNoSoportado):
        await caso.ejecutar(comando(organo=Organo.FRUTO))
    assert repo.datos == {}


async def test_imagen_rechazada_por_el_inspector_no_llega_al_modelo():
    detector = DetectorFalso()
    almacen = AlmacenEnMemoria()
    caso = DiagnosticarImagen(
        inspector=InspectorQueRechaza(),
        detectores=ProveedorDetectoresFalso({Organo.HOJA: detector}),
        almacen=almacen, repositorio=RepoEnMemoria(),
        reloj=RelojFijo(), ids=IdsSecuenciales(), umbral_confianza=0.35,
    )

    with pytest.raises(ImagenInvalida):
        await caso.ejecutar(comando())
    assert detector.recibidas == []
    assert almacen.objetos == {}


async def test_mime_no_permitido_falla_en_el_dominio(diagnosticar, detector_hoja):
    with pytest.raises(ImagenInvalida):
        await diagnosticar.ejecutar(comando(tipo_mime="image/gif"))
    assert detector_hoja.recibidas == []
```

```python
# tests/unit/diagnostico/test_obtener_diagnostico.py
import pytest

from plagas.modules.diagnostico.application.use_cases.obtener_diagnostico import ObtenerDiagnostico
from plagas.modules.diagnostico.domain.errors import DiagnosticoNoEncontrado

from ...factories import AGRICULTOR, OTRO_AGRICULTOR, TECNICO, comando


@pytest.fixture
async def diagnostico_de_agricultor(diagnosticar):
    return await diagnosticar.ejecutar(comando(propietario=AGRICULTOR))


async def test_el_dueno_ve_su_diagnostico(repo, diagnostico_de_agricultor):
    resultado = await ObtenerDiagnostico(repo).ejecutar(diagnostico_de_agricultor.id, AGRICULTOR)
    assert resultado.id == diagnostico_de_agricultor.id


async def test_un_tecnico_ve_diagnosticos_ajenos(repo, diagnostico_de_agricultor):
    resultado = await ObtenerDiagnostico(repo).ejecutar(diagnostico_de_agricultor.id, TECNICO)
    assert resultado.id == diagnostico_de_agricultor.id


async def test_otro_agricultor_recibe_no_encontrado_y_no_prohibido(repo, diagnostico_de_agricultor):
    # Mismo error que un ID inexistente: no se revela que el recurso existe (anti-IDOR)
    with pytest.raises(DiagnosticoNoEncontrado):
        await ObtenerDiagnostico(repo).ejecutar(diagnostico_de_agricultor.id, OTRO_AGRICULTOR)
```

### F.5 Pruebas de contrato (LSP) e integración

Una sola suite define el comportamiento que **todo** repositorio debe cumplir. Se hereda para el fake y para el adapter SQL; si el fake se comporta distinto que Postgres, los tests unitarios dejan de ser confiables y esta suite lo detecta.

```python
# tests/contract/test_repositorio_diagnosticos.py
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from plagas.modules.diagnostico.domain.entities import Diagnostico
from plagas.modules.diagnostico.domain.value_objects import Organo
from plagas.modules.diagnostico.infrastructure.repositorio_sqlalchemy import RepositorioDiagnosticosSql

from ..factories import deteccion
from ..fakes import RepoEnMemoria


def nuevo(minutos: int = 0) -> Diagnostico:
    return Diagnostico.registrar(
        id=uuid4(), propietario_id="u1", organo=Organo.FRUTO, imagen_ref="r",
        detecciones=[deteccion("sunblotch", 0.7)], umbral=0.35,
        ahora=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=minutos),
    )


class ContratoRepositorioDiagnosticos:
    """No empieza con 'Test': pytest no la recolecta sola, solo a través de sus hijas."""

    @pytest.fixture
    def repo(self):
        raise NotImplementedError

    async def test_por_id_inexistente_devuelve_none(self, repo):
        assert await repo.por_id(uuid4()) is None

    async def test_guardar_y_leer_conserva_todos_los_campos(self, repo):
        original = nuevo()
        await repo.guardar(original)
        leido = await repo.por_id(original.id)
        assert leido == original

    async def test_guardar_dos_veces_es_idempotente(self, repo):
        d = nuevo()
        await repo.guardar(d)
        await repo.guardar(d)
        assert len(await repo.recientes(limite=10, desplazamiento=0)) == 1

    async def test_recientes_ordena_del_mas_nuevo_al_mas_viejo_y_pagina(self, repo):
        viejos_a_nuevos = [nuevo(minutos=i) for i in range(5)]
        for d in viejos_a_nuevos:
            await repo.guardar(d)
        pagina = await repo.recientes(limite=2, desplazamiento=1)
        assert [d.id for d in pagina] == [viejos_a_nuevos[3].id, viejos_a_nuevos[2].id]


class TestRepoEnMemoria(ContratoRepositorioDiagnosticos):
    @pytest.fixture
    def repo(self):
        return RepoEnMemoria()


@pytest.mark.integration
class TestRepoSql(ContratoRepositorioDiagnosticos):
    @pytest.fixture
    def repo(self, sesion_db):
        return RepositorioDiagnosticosSql(sesion_db)
```

```python
# tests/integration/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from plagas.shared.infrastructure.db import Base


@pytest.fixture(scope="session")
def postgres_url():
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        yield pg.get_connection_url()


@pytest.fixture
async def sesion_db(postgres_url):
    engine = create_async_engine(postgres_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as sesion:
        yield sesion
    await engine.dispose()
```

> Para que `TestRepoSql` encuentre `sesion_db`, ese fixture se mueve a `tests/conftest.py` o se importa en `tests/contract/conftest.py`.

**Inspector de imágenes** (usa Pillow real; es rápido, así que corre en cada PR sin marcador):

```python
# tests/integration/test_inspector_pillow.py
import io

import pytest
from PIL import Image as PILImage

from plagas.modules.diagnostico.domain.errors import ImagenInvalida
from plagas.modules.diagnostico.domain.value_objects import Imagen
from plagas.modules.diagnostico.infrastructure.inspector_pillow import InspectorImagenesPillow


def codificar(img: PILImage.Image, formato: str, **kwargs) -> bytes:
    buffer = io.BytesIO()
    img.save(buffer, format=formato, **kwargs)
    return buffer.getvalue()


@pytest.fixture
def inspector():
    return InspectorImagenesPillow()


async def test_jpeg_valido_se_acepta_y_sale_como_jpeg(inspector):
    datos = codificar(PILImage.new("RGB", (640, 480), "green"), "JPEG")
    resultado = await inspector.sanear(Imagen(datos, "image/jpeg"))
    assert resultado.tipo_mime == "image/jpeg"
    assert resultado.contenido.startswith(b"\xff\xd8\xff")


async def test_elimina_metadatos_exif(inspector):
    exif = PILImage.Exif()
    exif[0x010F] = "MarcaDeCamara"          # Make
    exif[0x0110] = "ModeloDeCelular"        # Model
    datos = codificar(PILImage.new("RGB", (640, 480)), "JPEG", exif=exif)

    resultado = await inspector.sanear(Imagen(datos, "image/jpeg"))

    assert len(PILImage.open(io.BytesIO(resultado.contenido)).getexif()) == 0


async def test_png_declarado_como_jpeg_se_rechaza(inspector):
    datos = codificar(PILImage.new("RGB", (640, 480)), "PNG")
    with pytest.raises(ImagenInvalida):
        await inspector.sanear(Imagen(datos, "image/jpeg"))


async def test_html_disfrazado_de_imagen_se_rechaza(inspector):
    datos = b"<html><script>alert(1)</script></html>" + b" " * 200
    with pytest.raises(ImagenInvalida):
        await inspector.sanear(Imagen(datos, "image/png"))


async def test_jpeg_truncado_se_rechaza(inspector):
    datos = codificar(PILImage.new("RGB", (640, 480), "red"), "JPEG")
    with pytest.raises(ImagenInvalida):
        await inspector.sanear(Imagen(datos[: len(datos) // 2], "image/jpeg"))


async def test_bomba_de_descompresion_se_rechaza(inspector):
    # 8000x8000 px en modo 1-bit: pocos KB comprimidos, 64 MP al decodificar
    datos = codificar(PILImage.new("1", (8000, 8000)), "PNG")
    assert len(datos) < 200_000
    with pytest.raises(ImagenInvalida):
        await inspector.sanear(Imagen(datos, "image/png"))


async def test_imagen_demasiado_pequena_se_rechaza(inspector):
    datos = codificar(PILImage.new("RGB", (100, 100)), "JPEG")
    with pytest.raises(ImagenInvalida):
        await inspector.sanear(Imagen(datos, "image/jpeg"))
```

**Verificación de integridad de pesos:**

```python
# tests/unit/test_integridad.py
import hashlib

import pytest

from plagas.shared.infrastructure.integridad import PesosAlterados, verificar_sha256


def test_hash_correcto_no_lanza(tmp_path):
    archivo = tmp_path / "m.pt"
    archivo.write_bytes(b"pesos")
    verificar_sha256(archivo, hashlib.sha256(b"pesos").hexdigest())


def test_archivo_modificado_lanza(tmp_path):
    archivo = tmp_path / "m.pt"
    archivo.write_bytes(b"pesos-alterados")
    with pytest.raises(PesosAlterados):
        verificar_sha256(archivo, hashlib.sha256(b"pesos").hexdigest())
```

### F.6 Pruebas de la API (HTTP, seguridad y errores)

`ASGITransport` llama a la app en proceso, sin red. **No ejecuta el `lifespan`**, así que no se cargan los modelos ni se conecta a la BD: todo lo externo entra por `dependency_overrides`.

```python
# tests/api/conftest.py
import io
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image as PILImage

from plagas.config import Settings
from plagas.main import create_app
from plagas.modules.diagnostico.api.dependencies import get_diagnosticar_imagen
from plagas.shared.api.dependencias import get_container
from plagas.shared.api.seguridad import limiter

from ..factories import AGRICULTOR, TECNICO
from ..fakes import VerificadorFalso

TOKEN_AGRICULTOR = "token-agricultor"
TOKEN_TECNICO = "token-tecnico"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        env="dev",
        database_url="postgresql+asyncpg://no-se-usa/test",
        oidc_emisor="https://auth.test", oidc_jwks_url="https://auth.test/jwks",
        hosts_permitidos=["test"],
        sha256_modelo_hojas="0" * 64, sha256_modelo_frutos="0" * 64,
    )


@pytest.fixture
def app(settings, diagnosticar):
    app = create_app(settings)
    contenedor = SimpleNamespace(
        verificador_tokens=VerificadorFalso({TOKEN_AGRICULTOR: AGRICULTOR, TOKEN_TECNICO: TECNICO}),
    )
    app.dependency_overrides[get_container] = lambda: contenedor
    app.dependency_overrides[get_diagnosticar_imagen] = lambda: diagnosticar
    limiter.reset()
    return app


@pytest.fixture
async def cliente(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def jpeg() -> bytes:
    buffer = io.BytesIO()
    PILImage.new("RGB", (640, 480), "green").save(buffer, format="JPEG")
    return buffer.getvalue()


def auth(token: str = TOKEN_AGRICULTOR) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
```

```python
# tests/api/test_diagnosticos_api.py
from httpx import ASGITransport, AsyncClient

from plagas.modules.diagnostico.api.dependencies import get_obtener_diagnostico
from plagas.modules.diagnostico.application.use_cases.obtener_diagnostico import ObtenerDiagnostico
from plagas.shared.api.dependencias import get_container

from ..factories import OTRO_AGRICULTOR
from ..fakes import VerificadorFalso
from .conftest import TOKEN_AGRICULTOR, auth


def subir(jpeg: bytes, organo: str = "hoja", mime: str = "image/jpeg"):
    return {"data": {"organo": organo}, "files": {"imagen": ("foto.jpg", jpeg, mime)}}


async def test_crear_diagnostico_devuelve_201_con_el_contrato_esperado(cliente, jpeg):
    r = await cliente.post("/api/v1/diagnosticos", headers=auth(), **subir(jpeg))

    assert r.status_code == 201
    cuerpo = r.json()
    assert set(cuerpo) >= {"id", "organo", "es_sano", "enfermedades", "detecciones", "creado_en"}
    assert cuerpo["organo"] == "hoja"


async def test_respuesta_incluye_request_id_y_cabeceras_de_seguridad(cliente, jpeg):
    r = await cliente.post("/api/v1/diagnosticos", headers=auth(), **subir(jpeg))

    assert r.headers["X-Request-ID"]
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Cache-Control"] == "no-store"


# --- Autenticación ---------------------------------------------------------

async def test_sin_token_devuelve_401_problem_json(cliente, jpeg):
    r = await cliente.post("/api/v1/diagnosticos", **subir(jpeg))

    assert r.status_code == 401
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.headers["WWW-Authenticate"] == "Bearer"
    assert r.json()["title"] == "no_autenticado"


async def test_token_invalido_devuelve_401(cliente, jpeg):
    r = await cliente.post("/api/v1/diagnosticos", headers=auth("token-falso"), **subir(jpeg))
    assert r.status_code == 401


# --- Validación de entrada -------------------------------------------------

async def test_organo_desconocido_devuelve_422(cliente, jpeg):
    r = await cliente.post("/api/v1/diagnosticos", headers=auth(), **subir(jpeg, organo="raiz"))
    assert r.status_code == 422


async def test_mime_no_permitido_devuelve_422_con_codigo_estable(cliente, jpeg):
    r = await cliente.post("/api/v1/diagnosticos", headers=auth(), **subir(jpeg, mime="image/gif"))

    assert r.status_code == 422
    assert r.json()["title"] == "imagen_invalida"


async def test_cuerpo_mayor_al_limite_devuelve_413(cliente, settings):
    enorme = b"\xff\xd8\xff" + b"\x00" * settings.max_cuerpo_bytes
    r = await cliente.post("/api/v1/diagnosticos", headers=auth(), **subir(enorme))
    assert r.status_code == 413


async def test_host_no_permitido_devuelve_400(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://evil.com") as c:
        r = await c.get("/health/live")
    assert r.status_code == 400


# --- Autorización ----------------------------------------------------------

async def test_diagnostico_ajeno_devuelve_404(cliente, app, jpeg, repo):
    creado = (await cliente.post("/api/v1/diagnosticos", headers=auth(), **subir(jpeg))).json()
    app.dependency_overrides[get_obtener_diagnostico] = lambda: ObtenerDiagnostico(repo)
    contenedor = app.dependency_overrides[get_container]()
    contenedor.verificador_tokens = VerificadorFalso({"otro": OTRO_AGRICULTOR})

    r = await cliente.get(f"/api/v1/diagnosticos/{creado['id']}", headers=auth("otro"))

    assert r.status_code == 404


async def test_el_dueno_si_ve_su_diagnostico(cliente, app, jpeg, repo):
    creado = (await cliente.post("/api/v1/diagnosticos", headers=auth(TOKEN_AGRICULTOR), **subir(jpeg))).json()
    app.dependency_overrides[get_obtener_diagnostico] = lambda: ObtenerDiagnostico(repo)

    r = await cliente.get(f"/api/v1/diagnosticos/{creado['id']}", headers=auth(TOKEN_AGRICULTOR))

    assert r.status_code == 200


# --- Rate limiting ---------------------------------------------------------

async def test_mas_de_10_diagnosticos_por_minuto_devuelve_429(cliente, jpeg):
    for _ in range(10):
        assert (await cliente.post("/api/v1/diagnosticos", headers=auth(), **subir(jpeg))).status_code == 201

    r = await cliente.post("/api/v1/diagnosticos", headers=auth(), **subir(jpeg))

    assert r.status_code == 429
    assert r.json()["title"] == "limite_excedido"
```

### F.7 Regresión del modelo

Los tests de código no detectan que un peso nuevo **empeoró** el modelo. Hay dos controles:

1. **En `ml/` (antes de promover pesos):** `yolo val` sobre el split `test` y comparar con el `manifest.json` vigente. No se promueve si el mAP50-95 baja más de 1 punto o si alguna clase cae más de 5 puntos de recall.
2. **En `backend/` (golden set):** 2-3 imágenes por clase en `tests/fixtures/imagenes/`, tomadas del split `test` (nunca de `train`), con la clase esperada.

```python
# tests/modelo/test_regresion_yolo.py
from pathlib import Path

import pytest

from plagas.modules.diagnostico.domain.value_objects import Imagen
from plagas.modules.diagnostico.infrastructure.yolo_detector import DetectorYolo

pytestmark = pytest.mark.modelo

MODELOS = Path("models")
FIXTURES = Path(__file__).parent.parent / "fixtures" / "imagenes"

CASOS = [
    ("hojas.pt", "hoja/antracnosis_01.jpg", "antracnosis_hoja"),
    ("hojas.pt", "hoja/deficiencia_01.jpg", "deficiencia_nutricional"),
    ("hojas.pt", "hoja/plaga_01.jpg", "plaga"),
    ("frutos.pt", "fruto/cercospora_01.jpg", "cercospora"),
    ("frutos.pt", "fruto/rona_01.jpg", "rona"),
    ("frutos.pt", "fruto/sunblotch_01.jpg", "sunblotch"),
]


@pytest.fixture(scope="module")
def detectores():
    return {nombre: DetectorYolo(MODELOS / nombre) for nombre in {"hojas.pt", "frutos.pt"}}


@pytest.mark.parametrize(("pesos", "archivo", "clase_esperada"), CASOS)
async def test_detecta_la_clase_esperada(detectores, pesos, archivo, clase_esperada):
    imagen = Imagen((FIXTURES / archivo).read_bytes(), "image/jpeg")

    detecciones = await detectores[pesos].detectar(imagen)

    clases = {d.clase for d in detecciones if d.confianza.valor >= 0.35}
    assert clase_esperada in clases


async def test_las_cajas_salen_normalizadas(detectores):
    imagen = Imagen((FIXTURES / "hoja/antracnosis_01.jpg").read_bytes(), "image/jpeg")
    for d in await detectores["hojas.pt"].detectar(imagen):
        assert 0 <= d.caja.x1 < d.caja.x2 <= 1
        assert 0 <= d.caja.y1 < d.caja.y2 <= 1
```

### F.8 Pruebas del frontend

```ts
// vitest.config.ts
import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config';

export default mergeConfig(viteConfig, defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    coverage: {
      provider: 'v8',
      include: ['src/core/**', 'src/features/**/model/**', 'src/features/**/hooks/**'],
      thresholds: { lines: 80, branches: 80 },
    },
  },
}));
```

```ts
// src/test/setup.ts
import '@testing-library/jest-dom/vitest';
import { afterAll, afterEach, beforeAll } from 'vitest';
import { server } from './msw/server';

// Antes de que cualquier test importe core/config/env.ts
window.__APP_CONFIG__ = { apiBaseUrl: 'http://api.test', authUrl: 'http://auth.test', env: 'dev' };

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));   // ninguna llamada real a la red
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

```ts
// src/test/msw/handlers.ts
import { http, HttpResponse } from 'msw';

export const API = 'http://api.test';

export const diagnosticoEnfermo = {
  id: '00000000-0000-0000-0000-000000000001',
  organo: 'fruto',
  es_sano: false,
  enfermedades: ['cercospora'],
  detecciones: [{ clase: 'cercospora', confianza: 0.82, caja: { x1: 0.1, y1: 0.2, x2: 0.4, y2: 0.5 } }],
  imagen_url: 'https://almacen.test/x.jpg',
  creado_en: '2026-10-06T12:00:00Z',
};

export const handlers = [
  http.post(`${API}/api/v1/diagnosticos`, () => HttpResponse.json(diagnosticoEnfermo, { status: 201 })),
];

// src/test/msw/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';
export const server = setupServer(...handlers);
```

**Validación (Zod):**

```ts
// src/features/diagnostico/model/schemas.test.ts
import { describe, expect, it } from 'vitest';
import { DiagnosticoFormSchema } from './schemas';

const archivo = (tipo: string, bytes = 1024) =>
  new File([new Uint8Array(bytes)], 'foto', { type: tipo });

describe('DiagnosticoFormSchema', () => {
  it('acepta un JPEG de hoja', () => {
    expect(DiagnosticoFormSchema.safeParse({ organo: 'hoja', imagen: archivo('image/jpeg') }).success).toBe(true);
  });

  it.each(['image/gif', 'application/pdf', 'text/html'])('rechaza %s', (tipo) => {
    expect(DiagnosticoFormSchema.safeParse({ organo: 'hoja', imagen: archivo(tipo) }).success).toBe(false);
  });

  it('rechaza imágenes de más de 10 MB', () => {
    const r = DiagnosticoFormSchema.safeParse({ organo: 'fruto', imagen: archivo('image/jpeg', 11 * 1024 * 1024) });
    expect(r.success).toBe(false);
  });

  it('rechaza órganos desconocidos', () => {
    expect(DiagnosticoFormSchema.safeParse({ organo: 'raiz', imagen: archivo('image/jpeg') }).success).toBe(false);
  });
});
```

**Cliente HTTP y errores:**

```ts
// src/core/http/api-error.test.ts
import { describe, expect, it } from 'vitest';
import { ApiError } from './api-error';

describe('ApiError.desde', () => {
  it('lee un problem+json del backend', () => {
    const e = ApiError.desde(
      { title: 'imagen_invalida', status: 422, detail: 'Formato no soportado', request_id: 'abc' }, 422,
    );
    expect(e).toMatchObject({ status: 422, codigo: 'imagen_invalida', requestId: 'abc' });
  });

  it('degrada con elegancia si la respuesta no es problem+json', () => {
    const e = ApiError.desde('<html>Bad Gateway</html>', 502);
    expect(e).toMatchObject({ status: 502, codigo: 'desconocido' });
  });
});
```

**Hook con MSW** (verifica también que se envía el token):

```tsx
// src/features/diagnostico/hooks/useDiagnosticar.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import type { ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/core/http/api-error';
import { API } from '@/test/msw/handlers';
import { server } from '@/test/msw/server';
import { useDiagnosticar } from './useDiagnosticar';

vi.mock('@/core/auth/sesion', () => ({ obtenerToken: async () => 'token-test' }));

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

const imagen = new File([new Uint8Array(10)], 'f.jpg', { type: 'image/jpeg' });

describe('useDiagnosticar', () => {
  it('envía multipart con el token y devuelve el diagnóstico', async () => {
    let autorizacion: string | null = null;
    let organo: FormDataEntryValue | null = null;
    server.use(
      http.post(`${API}/api/v1/diagnosticos`, async ({ request }) => {
        autorizacion = request.headers.get('Authorization');
        organo = (await request.formData()).get('organo');
        return HttpResponse.json({ id: '1', enfermedades: ['cercospora'] }, { status: 201 });
      }),
    );

    const { result } = renderHook(() => useDiagnosticar(), { wrapper });
    result.current.mutate({ organo: 'fruto', imagen });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(autorizacion).toBe('Bearer token-test');
    expect(organo).toBe('fruto');
    expect(result.current.data?.enfermedades).toEqual(['cercospora']);
  });

  it('expone un ApiError con el código del backend', async () => {
    server.use(
      http.post(`${API}/api/v1/diagnosticos`, () =>
        HttpResponse.json(
          { title: 'imagen_invalida', status: 422, detail: 'Formato no soportado' },
          { status: 422, headers: { 'Content-Type': 'application/problem+json' } },
        ),
      ),
    );

    const { result } = renderHook(() => useDiagnosticar(), { wrapper });
    result.current.mutate({ organo: 'hoja', imagen });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(ApiError);
    expect((result.current.error as ApiError).codigo).toBe('imagen_invalida');
  });
});
```

**Componente / página** (se prueba como lo usa el agricultor: por roles y textos, no por clases CSS):

```tsx
// src/features/diagnostico/pages/DiagnosticoPage.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { DiagnosticoPage } from './DiagnosticoPage';

vi.mock('@/core/auth/sesion', () => ({ obtenerToken: async () => 'token-test' }));

function renderizar() {
  const qc = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  return render(<QueryClientProvider client={qc}><DiagnosticoPage /></QueryClientProvider>);
}

describe('DiagnosticoPage', () => {
  it('muestra la enfermedad detectada tras subir una foto de fruto', async () => {
    const usuario = userEvent.setup();
    renderizar();

    await usuario.click(screen.getByRole('radio', { name: /fruto/i }));
    await usuario.upload(
      screen.getByLabelText(/foto/i),
      new File([new Uint8Array(10)], 'palta.jpg', { type: 'image/jpeg' }),
    );
    await usuario.click(screen.getByRole('button', { name: /diagnosticar/i }));

    expect(await screen.findByText(/cercospora/i)).toBeInTheDocument();
  });

  it('no permite enviar sin elegir órgano ni imagen', async () => {
    renderizar();
    expect(screen.getByRole('button', { name: /diagnosticar/i })).toBeDisabled();
  });
});
```

### F.9 E2E (Playwright)

Pocos y estables, contra **staging** después de cada despliegue, con un usuario de prueba del proveedor OIDC:

1. Login → elegir *Fruto* → subir `fixtures/fruto/cercospora_01.jpg` → ver "Cercospora" y al menos una caja dibujada.
2. Abrir *Historial* → el diagnóstico recién creado aparece primero.
3. Abrir por URL el diagnóstico de **otro** usuario → página "No encontrado".

### F.10 Comandos

```makefile
test:              ## rápidas (unit + contract fake + api + inspector) — cada commit
	cd backend && uv run pytest
	cd frontend && npm test -- --run
test-integracion:  ## requiere Docker
	cd backend && uv run pytest -m integration --no-cov
test-modelo:       ## requiere models/*.pt
	cd backend && uv run pytest -m modelo --no-cov
cobertura:
	cd backend && uv run pytest --cov-report=html
	cd frontend && npx vitest run --coverage
```

---

## Anexo: flujo completo de un diagnóstico

```
[React] SelectorOrgano + CapturaImagen
   │  Zod valida (órgano, MIME, ≤10 MB)
   ▼
useDiagnosticar ──► apiClient.POST /api/v1/diagnosticos (multipart)
                                   │
[FastAPI] RequestContextMiddleware (request_id)
   ▼
router.crear_diagnostico  ── construye DiagnosticarImagenCommand
   ▼
DiagnosticarImagen.ejecutar
   ├─ Imagen(...)                          dominio valida invariantes
   ├─ ProveedorDetectores.para(organo) ──► DetectorYolo (hojas.pt | frutos.pt)
   ├─ detector.detectar(imagen)            hilo aparte, cajas normalizadas
   ├─ AlmacenImagenes.guardar(imagen)  ──► disco / S3
   ├─ Diagnostico.registrar(...)           aplica umbral, calcula es_sano
   └─ EscrituraDiagnosticos.guardar ─────► Postgres
   ▼
DiagnosticoResponse (Pydantic) ──► JSON
   ▼
[React] VisorDetecciones dibuja cajas · catálogo muestra recomendaciones por enfermedad
```
