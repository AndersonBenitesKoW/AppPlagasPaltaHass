from plagas.shared.domain.errors import ErrorDominio


class ImagenInvalida(ErrorDominio):
    codigo = "imagen_invalida"


class OrganoNoSoportado(ErrorDominio):
    codigo = "organo_no_soportado"


class DiagnosticoNoEncontrado(ErrorDominio):
    codigo = "diagnostico_no_encontrado"


class ConfianzaInvalida(ErrorDominio):
    codigo = "confianza_invalida"

    def __init__(self, valor: float) -> None:
        super().__init__(f"Confianza fuera de rango [0, 1]: {valor}")
