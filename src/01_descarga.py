"""Etapa 01 — Conexión y descarga de datos Sentinel-2 vía openEO
(ejercicios 1 y 2).

Conecta con Copernicus Data Space (openEO), y para cada lago y cada fecha
oficial descarga SOLO las bandas necesarias (B03, B04, B05, B08, SCL)
recortadas al bbox del lago. Salida: data/raw/<lago>/<fecha>.nc

Requiere una cuenta gratuita en https://dataspace.copernicus.eu — la primera
ejecución abre el navegador para autenticarse (OIDC device flow).
"""
import datetime as dt

import openeo

from config import BANDAS, COLECCION, DATA_RAW, LAGOS, OPENEO_URL
from utils import generar_geojsons


def conectar() -> openeo.Connection:
    conn = openeo.connect(OPENEO_URL).authenticate_oidc()
    print(f"✓ conectado a {OPENEO_URL}")
    return conn


def descargar_lago(conn, clave: str, lago: dict):
    destino = DATA_RAW / clave
    destino.mkdir(parents=True, exist_ok=True)
    bbox = lago["bbox"]
    for fecha in lago["fechas"]:
        salida = destino / f"{fecha}.nc"
        if salida.exists():
            print(f"  ya existe {salida.name}, omitiendo")
            continue
        # ventana [fecha, fecha+1) para capturar exactamente esa escena
        fin = (dt.date.fromisoformat(fecha) + dt.timedelta(days=1)).isoformat()
        cubo = conn.load_collection(
            COLECCION,
            spatial_extent=bbox,
            temporal_extent=[fecha, fin],
            bands=BANDAS,
        )
        print(f"  descargando {clave} {fecha}...")
        cubo.download(salida)
        print(f"  ✓ {salida.name}")


def main():
    generar_geojsons()
    conn = conectar()
    for clave, lago in LAGOS.items():
        print(f"\n== {lago['nombre']} ==")
        descargar_lago(conn, clave, lago)


if __name__ == "__main__":
    main()
