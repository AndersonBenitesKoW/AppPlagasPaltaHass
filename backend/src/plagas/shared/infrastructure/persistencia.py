import shutil
from pathlib import Path

import structlog
from sqlalchemy.engine import make_url

log = structlog.get_logger()

# Copias que viajan dentro de la imagen de Docker (versionadas en git).
DB_EMPAQUETADA = Path("plagas.db")
IMAGENES_EMPAQUETADAS = Path("data/imagenes")


def sembrar_datos_iniciales(database_url: str, almacen_dir: Path) -> None:
    """Copia la base y las imágenes empaquetadas a un volumen persistente en su primer arranque.

    En Railway el disco del contenedor se pierde en cada reinicio: si la base vive dentro de
    la imagen, todo lo borrado o creado vuelve al estado del último despliegue. Cuando
    APP_DATABASE_URL apunta a un volumen montado, la primera vez se siembra con los datos
    empaquetados y desde entonces el volumen es la única fuente de verdad.
    """
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database:
        return
    destino = Path(url.database)
    if destino.exists() or not DB_EMPAQUETADA.is_file():
        return
    if destino.resolve() == DB_EMPAQUETADA.resolve():
        return

    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DB_EMPAQUETADA, destino)

    copiadas = 0
    if IMAGENES_EMPAQUETADAS.is_dir() and almacen_dir.resolve() != IMAGENES_EMPAQUETADAS.resolve():
        almacen_dir.mkdir(parents=True, exist_ok=True)
        for origen in IMAGENES_EMPAQUETADAS.iterdir():
            if origen.is_file() and not (almacen_dir / origen.name).exists():
                shutil.copy2(origen, almacen_dir / origen.name)
                copiadas += 1

    log.info("datos_sembrados", base=str(destino), imagenes=copiadas)
