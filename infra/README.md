# infra/

Configuración de plataforma que **no** se despliega junto a la app:

- `keycloak/realm-plagas.json` — realm con roles y usuarios de prueba,
  importado automáticamente por la imagen de Keycloak en compose.

## Keycloak (desarrollo)

Tres usuarios precargados (contraseña `plagas`):

| Usuario | Rol | Puede |
|---|---|---|
| `agricultor1` | `agricultor` | Crear/ver/borrar sus diagnósticos |
| `tecnico1` | `tecnico` | Lo anterior + ver diagnósticos de todos |
| `admin1` | `admin` | Lo anterior + gestionar el catálogo |

Cliente frontend (público, Auth Code + PKCE): `app-plagas-frontend`.
Cliente backend (bearer-only): `api-plagas` (secreto dev: `plagas-secret-dev-only`).

En producción estos secretos se sustituyen por valores del gestor de
secretos; el `realm-plagas.json` de prod no se versiona.
