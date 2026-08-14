"""Etapa 04 — Análisis espacial de la cianobacteria (ejercicio 5).

Con los índices de la etapa 02 genera, para cada lago:
- Mapa interactivo folium con el índice de cianobacteria de cada fecha como
  capa activable (ejercicio 5.1) -> data/processed/mapas/<lago>.html
- Mapas comparativos entre fechas: primera escena, pico de floración y última
  escena, más el mapa de diferencia última-primera (ejercicio 5.2)
  -> data/processed/figuras/comparativo_<lago>.png
- Un resumen impreso de dónde se concentran los valores altos (norte/sur,
  este/oeste) como apoyo a la interpretación del ejercicio 5.3.

  python src/04_analisis_espacial.py
"""
import folium
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib import colors

from config import DATA_PROCESSED, FIGURAS, LAGOS, MAPAS, UMBRAL_CIANO_ALTO

# misma escala de color que la etapa 02 para que todo sea comparable
VMIN, VMAX = -0.1, 0.3
CMAP = "RdYlGn_r"  # verde = agua limpia, rojo = índice alto


def fechas_disponibles(clave: str, lago: dict) -> list[str]:
    return [f for f in lago["fechas"]
            if (DATA_PROCESSED / clave / f"{f}.nc").exists()]


def cargar_cyano(clave: str, fecha: str) -> xr.DataArray:
    return xr.open_dataset(DATA_PROCESSED / clave / f"{fecha}.nc")["cyano"]


def mapa_folium(clave: str, lago: dict, fechas: list[str]):
    """Mapa interactivo con una capa de cianobacteria por fecha."""
    bbox = lago["bbox"]
    centro = [(bbox["south"] + bbox["north"]) / 2,
              (bbox["west"] + bbox["east"]) / 2]
    m = folium.Map(location=centro, zoom_start=12, tiles="CartoDB positron")
    norm = colors.Normalize(vmin=VMIN, vmax=VMAX)
    cmap = plt.get_cmap(CMAP)
    for i, fecha in enumerate(fechas):
        ci = cargar_cyano(clave, fecha)
        rgba = cmap(norm(np.nan_to_num(ci.values, nan=VMIN)))
        # transparencia total fuera del agua para ver el mapa base
        rgba[..., 3] = np.where(np.isfinite(ci.values), 0.8, 0.0)
        folium.raster_layers.ImageOverlay(
            image=rgba,
            bounds=[[bbox["south"], bbox["west"]],
                    [bbox["north"], bbox["east"]]],
            name=f"NDCI {fecha}",
            show=(i == len(fechas) - 1),  # solo la última encendida al abrir
        ).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    MAPAS.mkdir(parents=True, exist_ok=True)
    salida = MAPAS / f"{clave}.html"
    m.save(salida)
    return salida


def mapas_comparativos(clave: str, lago: dict, fechas: list[str]):
    """Primera escena vs pico de floración vs última, y diferencia fin-inicio."""
    medias = {f: float(np.nanmean(cargar_cyano(clave, f).values))
              for f in fechas}
    pico = max(medias, key=medias.get)
    seleccion = list(dict.fromkeys([fechas[0], pico, fechas[-1]]))

    fig, axes = plt.subplots(1, len(seleccion) + 1, figsize=(4.6 * (len(seleccion) + 1), 4.2))
    for ax, fecha in zip(axes, seleccion):
        rol = " (pico)" if fecha == pico else ""
        cargar_cyano(clave, fecha).plot.imshow(
            ax=ax, vmin=VMIN, vmax=VMAX, cmap=CMAP,
            cbar_kwargs={"fraction": 0.046, "pad": 0.04, "label": "NDCI"})
        ax.set_title(f"{fecha}{rol}", fontsize=11)

    diff = cargar_cyano(clave, fechas[-1]) - cargar_cyano(clave, fechas[0])
    diff.plot.imshow(ax=axes[-1], vmin=-0.2, vmax=0.2, cmap="RdBu_r",
                     cbar_kwargs={"fraction": 0.046, "pad": 0.04, "label": "ΔNDCI"})
    axes[-1].set_title(f"Diferencia {fechas[-1]} − {fechas[0]}", fontsize=11)
    for ax in axes:
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")
    fig.suptitle(f"Comparación espacial de cianobacteria — {lago['nombre']}",
                 fontsize=13)
    fig.tight_layout()
    FIGURAS.mkdir(parents=True, exist_ok=True)
    salida = FIGURAS / f"comparativo_{clave}.png"
    fig.savefig(salida, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return salida, pico


def describir_concentracion(clave: str, lago: dict, fechas: list[str]):
    """Apoyo al ejercicio 5.3: en qué cuadrante del lago se concentra el índice
    alto y qué tan persistente es esa zona entre fechas."""
    conteo_alto = None
    n_validas = None
    for fecha in fechas:
        ci = cargar_cyano(clave, fecha)
        alto = (ci > UMBRAL_CIANO_ALTO).values
        valido = np.isfinite(ci.values)
        conteo_alto = alto.astype(int) if conteo_alto is None else conteo_alto + alto
        n_validas = valido.astype(int) if n_validas is None else n_validas + valido

    filas, cols = conteo_alto.shape
    mitades = {
        "norte": conteo_alto[: filas // 2].sum(),
        "sur": conteo_alto[filas // 2:].sum(),
        "oeste": conteo_alto[:, : cols // 2].sum(),
        "este": conteo_alto[:, cols // 2:].sum(),
    }
    # zona persistente: píxeles altos en la mayoría de fechas con datos
    with np.errstate(divide="ignore", invalid="ignore"):
        frec = np.where(n_validas > 0, conteo_alto / n_validas, 0)
    pct_persistente = 100 * float((frec >= 0.5).sum()) / max(int((n_validas > 0).sum()), 1)
    ns = "norte" if mitades["norte"] > mitades["sur"] else "sur"
    eo = "oeste" if mitades["oeste"] > mitades["este"] else "este"
    print(f"  valores altos concentrados hacia el {ns}-{eo} del lago")
    print(f"  {pct_persistente:.1f}% del agua supera el umbral en ≥50% de las fechas")


def main():
    for clave, lago in LAGOS.items():
        fechas = fechas_disponibles(clave, lago)
        print(f"\n== {lago['nombre']} ({len(fechas)} fechas) ==")
        if not fechas:
            print("  ⚠ sin índices procesados; correr antes 02_indices.py")
            continue
        html = mapa_folium(clave, lago, fechas)
        print(f"  ✓ mapa interactivo -> {html.name}")
        png, pico = mapas_comparativos(clave, lago, fechas)
        print(f"  ✓ mapas comparativos (pico {pico}) -> {png.name}")
        describir_concentracion(clave, lago, fechas)


if __name__ == "__main__":
    main()
