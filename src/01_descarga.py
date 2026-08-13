"""Etapa 01 — Conexión con la API de Sentinel-2 vía openEO (ejercicio 1).

Conecta con Copernicus Data Space (openEO). Requiere una cuenta gratuita en
https://dataspace.copernicus.eu — la primera ejecución abre el navegador
para autenticarse (OIDC device flow).
"""
import openeo

from config import COLECCION, OPENEO_URL


def conectar() -> openeo.Connection:
    conn = openeo.connect(OPENEO_URL).authenticate_oidc()
    print(f"✓ conectado a {OPENEO_URL}")
    print(conn.describe_collection(COLECCION)["description"][:200])
    return conn


def main():
    conectar()


if __name__ == "__main__":
    main()
