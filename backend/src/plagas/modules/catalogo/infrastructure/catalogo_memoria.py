from plagas.modules.catalogo.domain.entities import Enfermedad

DATOS_ENFERMEDADES: dict[str, Enfermedad] = {
    "hoja_sana": Enfermedad(
        codigo="hoja_sana",
        nombre="Hoja Sana",
        organo="hoja",
        severidad="nula",
        descripcion="La hoja muestra un aspecto saludable, turgente y con coloración verde uniforme, sin signos visibles de necrosis o invasión de plagas.",
        sintomas=(
            "Coloración verde homogénea",
            "Sin manchas necróticas",
            "Textura flexible y sana",
        ),
        recomendaciones=(
            "Continuar con el plan nutricional y de riego establecido.",
            "Mantener el monitoreo preventivo semanal en el lote.",
        ),
    ),
    "antracnosis_hoja": Enfermedad(
        codigo="antracnosis_hoja",
        nombre="Antracnosis en Hoja (Colletotrichum spp.)",
        organo="hoja",
        severidad="alta",
        descripcion="Infección fúngica causada principalmente por Colletotrichum gloeosporioides. Genera lesiones necróticas de color café a oscuro, a menudo iniciando en las puntas o márgenes foliares, favorecida por alta humedad.",
        sintomas=(
            "Manchas necróticas irregulares de color pardo o castaño oscuro",
            "Muerte regresiva o desecación en bordes de la lámina foliar",
            "Defoliación prematura en infestaciones severas",
        ),
        recomendaciones=(
            "Realizar podas sanitarias para mejorar la aireación e iluminación del dosel.",
            "Eliminar y destruir restos de hojas y ramas infectadas caídas al suelo.",
            "Aplicar tratamientos preventivos con sales de cobre (oxicloruro o hidróxido cúprico) en periodos de brotación y lluvias.",
            "Evitar el riego por aspersión que moje directamente el follaje.",
        ),
    ),
    "plaga": Enfermedad(
        codigo="plaga",
        nombre="Afección por Plagas (Trips, Arañita roja, Queresas)",
        organo="hoja",
        severidad="media",
        descripcion="Ataque de artrópodos plaga que succionan savia o raspan los tejidos de la hoja (comúnmente Oligonychus yothersi o Heliothrips haemorrhoidalis). Provoca decoloración, bronceado y pérdida de capacidad fotosintética.",
        sintomas=(
            "Punteaduras blanquecinas o aspecto bronceado/herrumbroso en el haz de la hoja",
            "Presencia de telarañas finas o mudas en el envés",
            "Bordes foliares curvados o deformados",
        ),
        recomendaciones=(
            "Evaluar el nivel de infestación mediante muestreo de hojas con lupa de 10x.",
            "Promover la fauna benéfica (crisopas, ácaros fitoseidos y mariquitas depredadoras).",
            "Aplicar lavados foliares con jabón potásico o aceites agrícolas minerales si la población supera el umbral económico.",
            "Mantener un buen estado hídrico del cultivo para reducir el estrés predisponente a ácaros.",
        ),
    ),
    "deficiencia_nutricional": Enfermedad(
        codigo="deficiencia_nutricional",
        nombre="Deficiencia Nutricional (Clorosis)",
        organo="hoja",
        severidad="media",
        descripcion="Trastorno abiótico ocasionado por la disponibilidad deficiente de nutrientes esenciales (típicamente nitrógeno, hierro, zinc o magnesio), afectando la síntesis de clorofila y el vigor del árbol.",
        sintomas=(
            "Clorosis intervenal (nervaduras verdes y lámina amarillenta)",
            "Hojas pequeñas, arrosetadas o con clorosis generalizada en hojas viejas",
            "Baja tasa de crecimiento vegetativo",
        ),
        recomendaciones=(
            "Realizar análisis foliar y de suelo para identificar el elemento limitante exacto.",
            "Ajustar el pH del suelo si se encuentra en rangos alcalinos que bloqueen el hierro y zinc.",
            "Aplicar fertilizaciones foliares con quelatos de zinc y hierro como medida de corrección rápida.",
            "Asegurar un programa de fertirriego balanceado acorde a la etapa fenológica del palto.",
        ),
    ),
}


class CatalogoEnMemoria:
    async def listar(self, organo: str | None = None) -> list[Enfermedad]:
        if organo:
            return [e for e in DATOS_ENFERMEDADES.values() if e.organo == organo]
        return list(DATOS_ENFERMEDADES.values())

    async def por_codigo(self, codigo: str) -> Enfermedad | None:
        return DATOS_ENFERMEDADES.get(codigo)
