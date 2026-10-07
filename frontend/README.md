# Frontend — plagas-palta-hass

App web de diagnóstico de plagas y enfermedades en palta Hass.

## Stack

- React 19, Vite 5, TypeScript 5 (strict)
- TanStack Query 5 (estado de servidor)
- Zod (validación de formularios y respuestas)
- openapi-fetch (cliente HTTP tipado desde el OpenAPI del backend)
- oidc-client-ts (Auth Code + PKCE; token solo en memoria)
- MSW 2 (mocks para tests)
- Playwright (E2E)

## Setup

```bash
npm install
cp .env.example .env.development.local
npm run dev
```

Por defecto, `npm run dev` arranca en `http://localhost:5173` y proxia `/api`
hacia `http://localhost:8000` (backend en local).

## Scripts

| Script              | Qué hace                                                 |
| ------------------- | -------------------------------------------------------- |
| `npm run dev`       | Vite dev server con HMR                                  |
| `npm run build`     | `tsc -b` + `vite build`                                  |
| `npm run preview`   | Sirve el build localmente                                |
| `npm run lint`      | ESLint (incluye `boundaries`)                            |
| `npm run typecheck` | `tsc --noEmit`                                           |
| `npm run test`      | Vitest en watch                                          |
| `npm run test:run`  | Vitest una vez                                           |
| `npm run test:cov`  | Con coverage                                             |
| `npm run gen:api`   | Regenera `core/http/schema.d.ts` desde `../openapi.json` |
| `npm run check:api` | Falla si el contrato cambió                              |
| `npm run e2e`       | Playwright contra el dev server                          |

## Estructura

```
src/
├── main.tsx              # entry point
├── app/                  # App.tsx, providers, router
├── test/                 # setup + MSW
├── core/                 # infraestructura transversal
│   ├── config/           # env (window.__APP_CONFIG__ + Zod)
│   ├── auth/             # OIDC + PKCE
│   ├── http/             # openapi-fetch + ApiError
│   └── logging/
├── shared/               # UI, hooks, lib (sin reglas de negocio)
│   ├── ui/               # Button, Card, Alert, FileDrop, Spinner
│   ├── hooks/
│   └── lib/
└── features/             # Screaming Architecture
    ├── diagnostico/      # captura + diagnóstico
    ├── historial/        # lista paginada de diagnósticos
    └── catalogo/         # enfermedades y recomendaciones
```

## Boundaries (eslint-plugin-boundaries)

| Desde        | Puede importar                              |
| ------------ | ------------------------------------------- |
| `app`        | `features`, `shared`, `core`                |
| `features/X` | `shared`, `core`, `features/X` (a sí misma) |
| `shared`     | solo `shared`                               |
| `core`       | solo `core`                                 |

Las features solo exponen su `index.ts` al resto de la app.
