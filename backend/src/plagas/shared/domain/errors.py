class ErrorDominio(Exception):
    """Base de errores de negocio. El 'codigo' es estable y consumido por el frontend."""

    codigo: str = "error_dominio"

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class NoAutenticado(ErrorDominio):
    codigo = "no_autenticado"


class SinPermiso(ErrorDominio):
    codigo = "sin_permiso"


class LimiteExcedido(ErrorDominio):
    codigo = "limite_excedido"


class ErrorInfraestructura(Exception):
    """Errores técnicos de almacenamiento, base de datos o inferencia."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
