"""Etapa 02 — Cálculo y visualización de índices espectrales (ejercicio 3).

Para cada escena descargada calcula, sobre el agua del lago, el índice de
cianobacteria (Cyano Detection Script = NDCI, bandas B04/B05), el NDVI (B04/B08)
y el NDWI (B03/B08), reproduciendo localmente el script de Sentinel Hub con las
bandas mínimas. Guarda los índices en data/processed/<lago>/<fecha>.nc y genera,
para cada lago, un mapa del índice de cianobacteria.

Como NDVI, NDWI y NDCI son cocientes normalizados de la forma (A-B)/(A+B), el
factor de escala de los valores digitales de Sentinel-2 se cancela y se pueden
calcular directamente sobre las bandas crudas. La máscara SCL==6 (agua) deja
fuera nubes, tierra y píxeles inválidos.

  python src/02_indices.py
"""
import glob

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from config import DATA_PROCESSED, DATA_RAW, LAGOS, MAPAS
from utils import calcular_indices

# escala común del índice de cianobacteria para que los mapas de un mismo lago
# sean comparables entre fechas
VMIN_CYANO, VMAX_CYANO = -0.1, 0.3
CMAP_CYANO = "RdYlGn_r"  # verde = agua limpia, rojo = índice alto


def escenas(clave: str):
    """Rutas de las escenas .nc de un lago, ordenadas por fecha."""
    return sorted(glob.glob(str(DATA_RAW / clave / "*.nc")))


def cargar_indices(ruta: str) -> xr.Dataset:
    """Abre una escena, quita la dimensión temporal y calcula los índices."""
    ds = xr.open_dataset(ruta).squeeze(drop=True)
    return calcular_indices(ds)


def guardar_indices(indices: xr.Dataset, clave: str, fecha: str):
    """Deja los índices en data/processed/<lago>/<fecha>.nc para la etapa 03."""
    destino = DATA_PROCESSED / clave
    destino.mkdir(parents=True, exist_ok=True)
    indices.to_netcdf(destino / f"{fecha}.nc")


def mapa_cyano_lago(clave: str, lago: dict, capas: list):
    """Panel con el índice de cianobacteria de todas las fechas del lago.

    Es el mapa del índice generado que pide el ejercicio 3, una vista por lago
    donde cada recuadro es una fecha y el color muestra la intensidad del índice
    sobre el agua.
    """
    n = len(capas)
    cols = 4
    filas = (n + cols - 1) // cols
    fig, axes = plt.subplots(filas, cols, figsize=(4 * cols, 3.4 * filas))
    axes = np.atleast_1d(axes).ravel()
    im = None
    for ax, (fecha, cyano) in zip(axes, capas):
        im = cyano.plot.imshow(
            ax=ax, add_colorbar=False, vmin=VMIN_CYANO, vmax=VMAX_CYANO, cmap=CMAP_CYANO
        )
        ax.set_title(fecha, fontsize=10)
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")
    for ax in axes[n:]:
        ax.axis("off")
    fig.suptitle(
        f"Índice de cianobacteria (NDCI) — {lago['nombre']}", fontsize=14, y=0.995
    )
    fig.tight_layout(rect=[0, 0.03, 1, 0.98])
    cbar = fig.colorbar(im, ax=axes.tolist(), fraction=0.02, pad=0.02)
    cbar.set_label("NDCI (más alto = más cianobacteria)")
    MAPAS.mkdir(parents=True, exist_ok=True)
    salida = MAPAS / f"cyano_{clave}.png"
    fig.savefig(salida, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return salida


def mapa_indices_fecha(clave: str, lago: dict, fecha: str, indices: xr.Dataset):
    """Compara NDVI, NDWI y NDCI de una misma escena, para evidenciar los tres.

    Se dibuja para la fecha de mayor índice de cianobacteria del lago, que es la
    más informativa.
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    paneles = [
        ("NDVI", indices["ndvi"], -0.2, 0.8, "YlGn"),
        ("NDWI", indices["ndwi"], -0.4, 0.6, "Blues"),
        ("NDCI (cianobacteria)", indices["cyano"], VMIN_CYANO, VMAX_CYANO, CMAP_CYANO),
    ]
    for ax, (titulo, da, vmin, vmax, cmap) in zip(axes, paneles):
        da.plot.imshow(ax=ax, vmin=vmin, vmax=vmax, cmap=cmap,
                       cbar_kwargs={"fraction": 0.046, "pad": 0.04})
        ax.set_title(titulo)
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")
    fig.suptitle(f"{lago['nombre']} — {fecha}", fontsize=13)
    fig.tight_layout()
    salida = MAPAS / f"indices_{clave}_{fecha}.png"
    fig.savefig(salida, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return salida


def procesar_lago(clave: str, lago: dict):
    rutas = escenas(clave)
    print(f"\n== {lago['nombre']} ({len(rutas)} escenas) ==")
    capas = []
    medias = {}
    for ruta in rutas:
        fecha = ruta.split("/")[-1].replace(".nc", "")
        indices = cargar_indices(ruta)
        guardar_indices(indices, clave, fecha)
        cyano = indices["cyano"]
        capas.append((fecha, cyano))
        agua = indices["agua"].values
        medias[fecha] = (indices, float(np.nanmean(cyano.values)))
        print(f"  {fecha}: agua={int(agua.sum())} px, NDCI medio={medias[fecha][1]:.4f}")

    salida = mapa_cyano_lago(clave, lago, capas)
    print(f"  ✓ mapa de cianobacteria -> {salida.name}")

    # panel NDVI/NDWI/NDCI en la fecha más crítica del lago
    fecha_pico = max(medias, key=lambda f: medias[f][1])
    salida2 = mapa_indices_fecha(clave, lago, fecha_pico, medias[fecha_pico][0])
    print(f"  ✓ índices NDVI/NDWI/NDCI ({fecha_pico}) -> {salida2.name}")


def main():
    for clave, lago in LAGOS.items():
        procesar_lago(clave, lago)
    print("\nÍndices calculados y mapas en", MAPAS)


if __name__ == "__main__":
    main()
