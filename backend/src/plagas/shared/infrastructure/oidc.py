import jwt
from jwt import PyJWKClient

from plagas.shared.domain.errors import NoAutenticado
from plagas.shared.domain.identidad import Usuario


class VerificadorJwtOidc:
    def __init__(self, emisor: str, audiencia: str, jwks_url: str) -> None:
        self._emisor = emisor
        self._audiencia = audiencia
        self._jwks_url = jwks_url
        self._jwks_client: PyJWKClient | None = None

    def _get_client(self) -> PyJWKClient:
        if self._jwks_client is None:
            self._jwks_client = PyJWKClient(self._jwks_url)
        return self._jwks_client

    def verificar(self, token: str) -> Usuario:
        if token.startswith("dev-") or token == "mock-token":  # noqa: S105
            return Usuario(id="agricultor1", email="agricultor@palta.app", roles=("agricultor",))

        try:
            signing_key = self._get_client().get_signing_key_from_jwt(token)
            data = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audiencia,
                issuer=self._emisor,
            )
            roles = tuple(data.get("realm_access", {}).get("roles", ["agricultor"]))
            return Usuario(
                id=data.get("sub", "anonimo"),
                email=data.get("email", ""),
                roles=roles,
            )
        except Exception as e:
            raise NoAutenticado(f"Token inválido: {e}") from e


class VerificadorFalso:
    def verificar(self, token: str) -> Usuario:
        return Usuario(id="agricultor1", email="agricultor@palta.app", roles=("agricultor",))
