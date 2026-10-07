# ADR 0001 — Monorepo para backend y frontend

**Estado:** Aceptado
**Fecha:** 2026-10-06
**Autores:** Equipo App Plagas Palta Hass

## Contexto

El sistema tiene un backend Python (FastAPI) y un frontend React que
comparten el contrato API. Se debe decidir la estrategia de repositorio.

## Decisión

Adoptar **monorepo** con la siguiente estructura raíz:

```
.
├── backend/      # FastAPI + Python
├── frontend/     # React + Vite
├── ml/           # Entrenamiento y datasets
├── docs/         # Documentación y ADRs
└── infra/        # Configuración de plataforma
```

## Consecuencias

**A favor:**
- Un solo PR puede tocar el contrato API (backend) y los tipos generados
  (frontend), evitando drift.
- El workflow de CI corre ambos lados en paralelo y puede hacer el
  chequeo de contrato en el mismo job.
- El versionado de `openapi.json` y `schema.d.ts` queda visible en el diff.
- `make up`, `make test`, `make lint` ejecutan todo desde la raíz.

**En contra:**
- El repo crece rápido (al agregar frontend con `node_modules` pesa más).
- Hay que enseñar las reglas de boundaries para que el frontend no
  importe del backend ni viceversa.
- Sin cambios se duplican los `.env.example` por aplicación (mitigado
  con `.env` por directorio y secreto por entorno).

## Alternativas consideradas

- **Dos repos separados:** más limpio pero rompe el contrato al tener
  PRs descoordinados. Descartado.
- **Backend como submódulo del frontend:** invierte la jerarquía. Descartado.
