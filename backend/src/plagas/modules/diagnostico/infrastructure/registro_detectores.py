from plagas.modules.diagnostico.application.ports import DetectorEnfermedades
from plagas.modules.diagnostico.domain.errors import OrganoNoSoportado
from plagas.modules.diagnostico.domain.value_objects import Organo


class RegistroDetectores:
    """Implementa ProveedorDetectores. Asocia cada Organo a su DetectorEnfermedades."""

    def __init__(self, detectores: dict[Organo, DetectorEnfermedades]) -> None:
        self._detectores = dict(detectores)

    def para(self, organo: Organo) -> DetectorEnfermedades:
        detector = self._detectores.get(organo)
        if detector is None:
            raise OrganoNoSoportado(f"No hay detector disponible para el órgano: '{organo}'")
        return detector
