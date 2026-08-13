"""Funciones compartidas del pipeline del Laboratorio 4."""
import json

import numpy as np
import xarray as xr

from config import GEOJSON_DIR, LAGOS


def bbox_a_geojson(bbox: dict) -> dict:
    """Convierte un bbox {west, east, south, north} a un Feature GeoJSON."""
    w, e, s, n = bbox["west"], bbox["east"], bbox["south"], bbox["north"]
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[w, s], [e, s], [e, n], [w, n], [w, s]]],
            },
        }],
    }


def generar_geojsons():
    """Escribe los GeoJSON de ambos lagos en data/raw/geojson/."""
    GEOJSON_DIR.mkdir(parents=True, exist_ok=True)
    for clave, lago in LAGOS.items():
        ruta = GEOJSON_DIR / f"{clave}.geojson"
        ruta.write_text(json.dumps(bbox_a_geojson(lago["bbox"]), indent=2))
        print(f"✓ {ruta}")


def mascara_agua(ds: xr.Dataset) -> xr.DataArray:
    """Máscara de agua: SCL==6 (agua) y NDWI positivo como respaldo."""
    ndwi = (ds["B03"] - ds["B08"]) / (ds["B03"] + ds["B08"])
    if "SCL" in ds:
        return (ds["SCL"] == 6) | (ndwi > 0.2)
    return ndwi > 0.2


def calcular_indices(ds: xr.Dataset) -> xr.Dataset:
    """Calcula NDVI, NDWI y el índice de cianobacteria (NDCI).

    Reproduce localmente el Cyano Detection Script de
    https://custom-scripts.sentinel-hub.com (basado en NDCI, bandas B04/B05):
        NDCI = (B05 - B04) / (B05 + B04)
    Valores altos de NDCI sobre agua indican concentración de clorofila-a
    asociada a floraciones de cianobacteria.
    """
    out = xr.Dataset()
    out["ndvi"] = (ds["B08"] - ds["B04"]) / (ds["B08"] + ds["B04"])
    out["ndwi"] = (ds["B03"] - ds["B08"]) / (ds["B03"] + ds["B08"])
    out["cyano"] = (ds["B05"] - ds["B04"]) / (ds["B05"] + ds["B04"])
    agua = mascara_agua(ds)
    # los índices de agua solo tienen sentido dentro del lago
    out["cyano"] = out["cyano"].where(agua)
    out["agua"] = agua
    return out


def stats_por_fecha(da: xr.DataArray) -> dict:
    """Estadísticas básicas de un índice (ignora NaN fuera del lago)."""
    v = da.values
    v = v[np.isfinite(v)]
    return {
        "media": float(np.mean(v)) if v.size else np.nan,
        "mediana": float(np.median(v)) if v.size else np.nan,
        "p90": float(np.percentile(v, 90)) if v.size else np.nan,
        "max": float(np.max(v)) if v.size else np.nan,
        "n_pixeles": int(v.size),
    }
