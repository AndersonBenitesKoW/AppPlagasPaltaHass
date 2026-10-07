# ADR 0003 — Screaming Architecture en frontend

**Estado:** Aceptado
**Fecha:** 2026-10-06
**Autores:** Equipo App Plagas Palta Hass

## Contexto

El frontend es pequeño pero crecerá (diagnóstico, historial, catálogo,
futuras alertas). Una organización por tipo técnico (`components/`,
`hooks/`, `pages/`) obliga a saltar entre carpetas para entender una
feature.

## Decisión

Adoptar **Screaming Architecture**: el árbol "grita" el negocio.

```
src/features/
├── diagnostico/   # captura + diagnóstico
├── historial/     # lista de diagnósticos
└── catalogo/      # enfermedades
```

Cada feature se organiza por responsabilidad técnica (`api/`, `model/`,
`hooks/`, `components/`, `pages/`) y expone solo un `index.ts` público.

La infraestructura transversal vive en `core/` (env, http, auth, logging)
y la UI reutilizable en `shared/`.

Las dependencias entre grupos se **fuerzan con ESLint
(`eslint-plugin-boundaries`)**:

| Desde   | Puede importar                               |
|---------|----------------------------------------------|
| `app`   | `features`, `shared`, `core`                 |
| `features/X` | `shared`, `core`, `features/X` (a sí misma) |
| `shared`| solo `shared`                                |
| `core`  | solo `core`                                  |

## Consecuencias

**A favor:**
- Una feature nueva = una carpeta nueva + un `lazy()` en el router.
- Las features no se acoplan entre sí; comunicación por `core/`
  (auth, http).
- El equipo entiende el dominio abriendo `features/`.

**En contra:**
- Hay que mover archivos cuando algo pasa de compartido a feature
  específica.
- `shared/` puede convertirse en "cajón de sastre"; revisión periódica.

## Alternativas consideradas

- **Atomic Design:** útil para design systems, no para apps con estado
  de servidor. Descartado.
- **Por tipo técnico (components/, hooks/, pages/):** clásico pero
  confunde a nuevos miembros. Descartado.
