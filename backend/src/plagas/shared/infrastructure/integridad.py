import hashlib
from pathlib import Path

from plagas.shared.domain.errors import ErrorInfraestructura


def verificar_sha256(ruta: Path, esperado: str) -> None:
    """Verifica que el hash SHA-256 del archivo coincida con el esperado."""
    if not ruta.exists():
        raise ErrorInfraestructura(f"El archivo del modelo no existe: {ruta}")

    if not esperado or esperado.strip() == "" or set(esperado) == {"0"}:
        # En dev si no está configurado un sha estricto, permitimos continuar
        return

    sha = hashlib.sha256()
    with ruta.open("rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)

    calculado = sha.hexdigest().lower()
    if calculado != esperado.lower():
        raise ErrorInfraestructura(
            f"Integridad comprometida en {ruta.name}: se esperaba {esperado}, calculado {calculado}"
        )
