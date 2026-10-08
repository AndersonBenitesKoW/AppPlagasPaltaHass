from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )

    env: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./plagas.db"

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
    ]

    modelos_dir: Path = Path("models")
    modelo_hojas: str = "hojas.pt"
    modelo_frutos: str = "frutos.pt"
    yolo_imgsz: int = 1024
    umbral_confianza: float = 0.35

    almacen: Literal["local", "s3"] = "local"
    almacen_local_dir: Path = Path("./data/imagenes")
    s3_bucket: str | None = None

    # Seguridad / OIDC
    oidc_emisor: str = "http://localhost:8081/realms/plagas"
    oidc_audiencia: str = "api-plagas"
    oidc_jwks_url: str = "http://localhost:8081/realms/plagas/protocol/openid-connect/certs"

    hosts_permitidos: list[str] = [
        "localhost",
        "127.0.0.1",
        "backend",
        "appplagaspaltahass-2.up.railway.app",
    ]

    max_cuerpo_bytes: int = 11 * 1024 * 1024
    rate_limit_storage: str = "memory://"

    sha256_modelo_hojas: str = ""
    sha256_modelo_frutos: str = ""
    retencion_dias: int = 365