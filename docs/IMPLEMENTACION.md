# Plan de implementación — App Plagas Palta Hass

Basado en [`ARQUITECTURA.md`](../ARQUITECTURA.md). **12 fases**, cada una
con criterio de "hecho" verificable.

## Decisiones confirmadas

- **Sin frutos.pt** por ahora: `Organo.FRUTO` levanta `OrganoNoSoportado`.
- **Solo AlmacenLocal**: el Protocol y el switch están listos para S3.
- **Keycloak real** en compose (Fase 7). Fases 1-6 usan `VerificadorFalso`.
- **Python 3.12** vía pyenv; Docker también 3.12-slim.

---

## Fase 0 — Prerrequisitos y migración inicial

- [ ] Instalar pyenv-win y bajar Python 3.12.x; `pyenv local 3.12`.
- [ ] Instalar Docker Desktop (para Fase 7+).
- [ ] Mover `scripts/`, `revision/`, `Dataset*`, notebook, `ESTRATEGIA_DATASET.md` a `ml/`.
- [ ] Copiar `bestHojas.pt` → `backend/models/hojas.pt`.
- [ ] Generar `backend/models/manifest.json` con SHA-256.
- [ ] Crear `.gitignore` raíz y por subproyecto.

**Hecho:** `git status` limpio, `pyenv local` 3.12.x, SHA-256 coincide con manifest.

---

## Fase 1 — Scaffolding del monorepo

- [ ] Estructura de carpetas completa (backend, frontend, ml, docs, infra).
- [ ] `backend/pyproject.toml` con deps, ruff, mypy strict, import-linter, pytest.
- [ ] `frontend/package.json` con React 19, Vite 5, TanStack Query, Zod, oidc-client-ts.
- [ ] `Makefile`, `docker-compose.yml`, `docker-compose.override.yml`.
- [ ] `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
- [ ] `eslint.config.js` con `eslint-plugin-boundaries`.
- [ ] `tsconfig.json` estricto.

**Hecho:** `uv sync` y `npm install` resuelven; `make lint` y `make test` corren.

---

## Fase 2 — Backend: shared kernel

- [ ] `shared/domain/errors.py`, `identidad.py`, `ports.py`.
- [ ] `shared/infrastructure/reloj.py`, `integridad.py`, `db.py`, `logging.py`, `oidc.py`.
- [ ] Tests unitarios en `tests/unit/shared/`.

**Hecho:** `uv run pytest tests/unit/shared` verde; cobertura ≥ 90%; mypy strict pasa.

---

## Fase 3 — Backend: módulo `diagnostico` (dominio + casos de uso)

- [ ] `modules/diagnostico/domain/{value_objects,entities,errors}.py`.
- [ ] `modules/diagnostico/application/{ports,dtos}.py`.
- [ ] `modules/diagnostico/application/use_cases/{diagnosticar_imagen,obtener_diagnostico,listar_historial}.py`.
- [ ] `tests/fakes.py` y `tests/factories.py`.
- [ ] Tests unitarios siguiendo §F.4 del ARQUITECTURA.md.

**Hecho:** `uv run pytest tests/unit` verde; cobertura dominio+application ≥ 90%; import-linter cumple.

---

## Fase 4 — Backend: infraestructura del módulo `diagnostico`

- [ ] `inspector_pillow.py` con magic bytes, EXIF, re-codificación.
- [ ] `yolo_detector.py` con `threading.Lock` y `anyio.to_thread`.
- [ ] `registro_detectores.py` con `ProveedorDetectores`.
- [ ] `almacen_local.py` con `AlmacenImagenes`.
- [ ] `orm.py`, `repositorio_sqlalchemy.py`, primera migración Alembic.
- [ ] Tests de integración con testcontainers Postgres.
- [ ] Contract tests del repositorio (LSP).

**Hecho:** `uv run pytest -m "not modelo"` verde; el contract test detecta divergencias.

---

## Fase 5 — Backend: API HTTP (transport + seguridad + errores)

- [ ] `modules/diagnostico/api/{schemas,router,dependencies}.py`.
- [ ] `shared/api/{errors,middlewares,seguridad,auth,dependencias,health}.py`.
- [ ] `config.py` con `Settings` validado por pydantic-settings.
- [ ] Tests API siguiendo §F.6 del ARQUITECTURA.md (9 tests).

**Hecho:** `uv run pytest tests/api` verde; `create_app()` sin YOLO (override).

---

## Fase 6 — Backend: composition root

- [ ] `container.py` con `Container.construir(settings)`.
- [ ] `main.py` con `create_app()` factory y `lifespan`.
- [ ] `pytest.ini` final con marcadores.
- [ ] Test de integración sin Docker.

**Hecho:** `uvicorn plagas.main:create_app --factory` arranca; `/health/live` 200; cobertura ≥ 80%.

---

## Fase 7 — Backend: contenedor, Keycloak y compose

- [ ] `backend/Dockerfile` multi-stage.
- [ ] Servicio Keycloak en compose con realm `plagas` importado.
- [ ] Volúmenes, healthchecks, `read_only`, `cap_drop ALL`.
- [ ] Verificación con `curl` real: 3 roles funcionando.

**Hecho:** `docker compose up` levanta el stack completo; auth OIDC real funciona.

---

## Fase 8 — Frontend: scaffolding + core

- [ ] Vite + TS estricto, ESLint con boundaries, Vitest + MSW.
- [ ] `core/config/env.ts` con Zod.
- [ ] `core/http/{client,api-error}.ts` con openapi-fetch.
- [ ] `core/auth/sesion.ts` con oidc-client-ts (Auth Code + PKCE).
- [ ] `shared/ui/{Button,Card,Spinner,Alert,FileDrop}.tsx`.
- [ ] Tests: ApiError, env, Button.

**Hecho:** `npm run lint && npm run typecheck && npm test` verde.

---

## Fase 9 — Frontend: feature `diagnostico`

- [ ] `model/schemas.ts` con Zod.
- [ ] `api/diagnostico.api.ts` con FormData.
- [ ] `hooks/{useDiagnosticar,useDiagnostico,useHistorial}.ts`.
- [ ] `components/{SelectorOrgano,CapturaImagen,VisorDetecciones}.tsx`.
- [ ] `pages/DiagnosticoPage.tsx`.
- [ ] Tests: schemas, hook, page.

**Hecho:** flujo "elegir hoja → subir foto → ver enfermedad" funciona contra MSW.

---

## Fase 10 — Frontend: features `historial` y `catalogo`

- [ ] Historial con paginación, filtro, botón eliminar.
- [ ] Catálogo con lista de enfermedades.
- [ ] `ErrorBoundary` global y `QueryCache.onError` para 401/403.

**Hecho:** las 3 features navegan entre sí; 401 redirige al login.

---

## Fase 11 — Backend: módulo `catalogo` y derecho de supresión

- [ ] Módulo `catalogo` con dominio, casos de uso, adapter, API.
- [ ] Seed inicial desde `data.yaml`.
- [ ] `DELETE /api/v1/diagnosticos/{id}` y `DELETE /api/v1/usuarios/yo/datos`.

**Hecho:** todos los endpoints del ARQUITECTURA.md están vivos.

---

## Fase 12 — CI/CD, E2E y checklist pre-prod

- [ ] GitHub Actions verde.
- [ ] E2E con Playwright (4 specs).
- [ ] `tests/modelo/test_regresion_yolo.py` con golden set.
- [ ] Checklist §E.10 firmado.

**Hecho:** un PR de ejemplo dispara CI y tarda < 8 min.

---

## Resumen

| Fase | Sesiones |
|---|---|
| 0 | 0.5 |
| 1 | 1 |
| 2 | 1 |
| 3 | 1.5 |
| 4 | 2 |
| 5 | 1.5 |
| 6 | 1 |
| 7 | 1.5 |
| 8 | 1.5 |
| 9 | 1.5 |
| 10 | 1 |
| 11 | 1.5 |
| 12 | 1.5 |
| **Total** | **~16 sesiones** |
