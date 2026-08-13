"""Configuración central del Laboratorio 4 — Datos Geoespaciales.

Coordenadas y fechas oficiales tomadas del enunciado del laboratorio
(CC3084, Semestre II 2026). Usar EXCLUSIVAMENTE estas fechas.
"""
from pathlib import Path

# ---------------------------------------------------------------- rutas
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
GEOJSON_DIR = DATA_RAW / "geojson"
FIGURAS = DATA_PROCESSED / "figuras"
MAPAS = DATA_PROCESSED / "mapas"

# ------------------------------------------------------- áreas de interés
LAGOS = {
    "atitlan": {
        "nombre": "Lago de Atitlán",
        "bbox": {"west": -91.326256, "east": -91.07151,
                 "south": 14.5948, "north": 14.750979},
        # 11 fechas oficiales (enunciado)
        "fechas": [
            "2025-01-18", "2025-04-13", "2025-05-13", "2025-07-17",
            "2025-11-21", "2025-12-29", "2026-02-12", "2026-03-24",
            "2026-04-13", "2026-04-28", "2026-07-22",
        ],
    },
    "amatitlan": {
        "nombre": "Lago de Amatitlán",
        "bbox": {"west": -90.638065, "east": -90.512924,
                 "south": 14.412347, "north": 14.493799},
        # 11 fechas oficiales; 2026-02-07 tiene cobertura parcial (~57.1%)
        "fechas": [
            "2025-01-28", "2025-04-15", "2025-04-28", "2025-11-24",
            "2026-01-08", "2026-02-02", "2026-02-07", "2026-03-29",
            "2026-04-13", "2026-04-28", "2026-06-19",
        ],
    },
}

# ------------------------------------------------------------- Sentinel-2
# Solo las bandas mínimas necesarias (enunciado, ejercicio 3.2):
#   NDVI: B04, B08 | NDWI: B03, B08 | Cyano: B03, B04, B05 (script Sentinel Hub)
#   SCL: máscara de nubes/clasificación de escena
BANDAS = ["B03", "B04", "B05", "B08", "SCL"]

OPENEO_URL = "openeo.dataspace.copernicus.eu"
COLECCION = "SENTINEL2_L2A"
MAX_CLOUD_COVER = 20  # las fechas oficiales ya están filtradas por nubosidad

# Umbral para considerar "valores altos" de cianobacteria (ejercicio 8.1).
# Se define sobre el índice NDCI; ajustar tras explorar la distribución.
UMBRAL_CIANO_ALTO = 0.1
