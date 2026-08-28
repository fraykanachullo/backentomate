"""
Diccionario de clases YOLOv8 - 5 clases del dataset Majes.
Fuente: doc_tecnica 2.2.2 y 4.3
"""

CLASS_NAMES = {
    0: "sana",
    1: "mildiu",
    2: "oidio",
    3: "mosca_blanca",
    4: "polilla",
}

# Reverse map
CLASS_IDS = {v: k for k, v in CLASS_NAMES.items()}

CLASS_METADATA = {
    "sana": {
        "label": "sana",
        "scientific": None,
        "spanish": "Planta sana",
        "description": "Sin signos visibles de enfermedad o plaga.",
        "recommendation": "Continuar monitoreo preventivo cada 7 dias.",
        "color": "#43A047",
    },
    "mildiu": {
        "label": "mildiu",
        "scientific": "Phytophthora infestans",
        "spanish": "Mildiu",
        "description": "Manchas oscuras humedas en hojas y frutos, tipico en alta humedad.",
        "recommendation": "Aplicar fungicida a base de mancozeb o clorotalonil, mejorar ventilacion.",
        "color": "#FF6B35",
    },
    "oidio": {
        "label": "oidio",
        "scientific": "Leveillula taurica",
        "spanish": "Oidío / Cenicilla",
        "description": "Polvo blanco en haz y enves de hojas, reduce fotosintesis.",
        "recommendation": "Azufre micronizado o bicarbonato potasico, evitar exceso de nitrogeno.",
        "color": "#F9A825",
    },
    "mosca_blanca": {
        "label": "mosca_blanca",
        "scientific": "Bemisia tabaci",
        "spanish": "Mosca blanca",
        "description": "Pequeños insectos blancos en enves, transmiten virus y fumagina.",
        "recommendation": "Trampas cromáticas amarillas, jabon potasico, control biologico con Encarsia.",
        "color": "#FF6B9D",
    },
    "polilla": {
        "label": "polilla",
        "scientific": "Tuta absoluta",
        "spanish": "Polilla del tomate",
        "description": "Minas y galerias en hojas, perforaciones en frutos.",
        "recommendation": "Feromonas, Bacillus thuringiensis, eliminar restos de cosecha.",
        "color": "#E53935",
    },
}

def get_metadata(label: str) -> dict:
    return CLASS_METADATA.get(label, {"label": label, "spanish": label, "scientific": None})
