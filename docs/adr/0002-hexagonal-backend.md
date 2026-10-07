# ADR 0002 — Clean Architecture hexagonal en backend

**Estado:** Aceptado
**Fecha:** 2026-10-06
**Autores:** Equipo App Plagas Palta Hass

## Contexto

El backend manipulará modelos ML (cambia el motor), almacenará en BD
(cambia el motor), autentica contra un proveedor externo (cambia el
proveedor) y expone una API HTTP. Si la lógica de negocio se mezcla
con estas dependencias, los cambios se propagan y rompen tests.

## Decisión

Adoptar **Clean Architecture / Hexagonal (Ports & Adapters)** con:

- `domain/`: entidades, value objects, errores, ports. Sin frameworks.
- `application/`: casos de uso y DTOs. Define los `Protocol` que
  el resto cumple.
- `infrastructure/`: adapters concretos (YOLO, SQLAlchemy, OIDC, Pillow,
  almacén local).
- `api/`: routers FastAPI, schemas Pydantic, dependencias.
- `container.py` (Composition Root): único archivo que conoce las
  clases concretas.

Regla: `api → application → domain`; `infrastructure` implementa
puertos y nunca es importado por `api` ni por `application`.

Las dependencias se **verifican en CI** con `import-linter` (4 contratos:
capas hexagonales, API no conoce infra, dominio puro, módulos
independientes).

## Consecuencias

**A favor:**
- Cambiar YOLO por ONNX Runtime o un servicio remoto = un nuevo adapter
  y una línea en `container.py`.
- Cambiar OIDC de Keycloak a Auth0 = un adapter nuevo.
- Los casos de uso se prueban con fakes sin tocar BD, red ni YOLO.

**En contra:**
- Más archivos y más capas que un MVC plano.
- Hay que entrenar al equipo en el flujo de dependencias (DIP).

## Alternativas consideradas

- **MVC plano:** más simple pero cualquier cambio toca varias capas.
- **DDD puro sin hexagonal:** comparte la mayoría del diseño, pero la
  separación ports/adapters hace explícita la inyección de dependencias.
