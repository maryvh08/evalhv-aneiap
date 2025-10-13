# indicators.py
import json
from typing import Dict, Any


# Ejemplo de estructura mínima de indicadores (usa mayúsculas para capítulos y códigos de cargo)
# Puedes sustituir esto con la lectura de un archivo JSON real (ver load_indicators).
DEFAULT_INDICATORS = {
    "UNIGUAJIRA": {
        "DCA": {
            "liderazgo": ["lider", "liderazgo", "coordinar", "dirigir"],
            "gestión": ["gestión", "gestionar", "administrar"],
            "docencia": ["docente", "profesor", "docencia"]
        },
        "DCC": {
            "comunicaciones": ["comunicación", "prensa", "boletín", "comunicados"],
            "redes": ["redes sociales", "facebook", "instagram", "twitter"]
        }
    },
    # agrega más capítulos y cargos...
}


def load_indicators_from_json(path: str) -> Dict[str, Any]:
    """
    Carga indicadores desde un archivo JSON. Si falla, devuelve DEFAULT_INDICATORS.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            else:
                return DEFAULT_INDICATORS
    except Exception as e:
        # fallback a default y loguear si hace falta
        print(f"⚠️ No se pudo cargar indicadores desde {path}: {e}. Usando DEFAULT_INDICATORS.")
        return DEFAULT_INDICATORS

