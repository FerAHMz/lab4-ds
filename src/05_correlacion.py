"""Etapa 05 — Correlación NDVI/NDWI vs cianobacteria (ejercicio 6).

Correlaciona el índice de cianobacteria (NDCI) con NDVI y NDWI de dos formas:
- Píxel a píxel dentro del agua de cada escena (Pearson y Spearman por fecha)
  -> data/processed/correlaciones.csv
- A nivel de medias por fecha, con un scatter por índice y lago
  -> data/processed/figuras/correlacion_medias.png

Imprime además un resumen por lago con el signo y la fuerza promedio de cada
relación, base para explicar los hallazgos (ejercicio 6.1).

  python src/05_correlacion.py
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from scipy import stats

from config import DATA_PROCESSED, FIGURAS, LAGOS


def correlacion_pixel(clave: str, lago: dict) -> list[dict]:
    """Pearson/Spearman entre NDCI y NDVI/NDWI, píxel a píxel por fecha."""
    filas = []
    for fecha in lago["fechas"]:
        ruta = DATA_PROCESSED / clave / f"{fecha}.nc"
        if not ruta.exists():
            continue
        ds = xr.open_dataset(ruta)
        ci = ds["cyano"].values.ravel()  # ya viene enmascarado al agua
        for indice in ("ndvi", "ndwi"):
            otro = ds[indice].values.ravel()
            ok = np.isfinite(ci) & np.isfinite(otro)
            if ok.sum() < 30:
                continue
            pearson = stats.pearsonr(ci[ok], otro[ok])
            spearman = stats.spearmanr(ci[ok], otro[ok])
            filas.append({
                "lago": clave, "fecha": fecha, "indice": indice,
                "pearson_r": pearson.statistic, "pearson_p": pearson.pvalue,
                "spearman_r": spearman.statistic, "spearman_p": spearman.pvalue,
                "n_pixeles": int(ok.sum()),
            })
    return filas


def medias_por_fecha() -> pd.DataFrame:
    """Media de cada índice por lago y fecha (para el scatter de medias)."""
    filas = []
    for clave, lago in LAGOS.items():
        for fecha in lago["fechas"]:
            ruta = DATA_PROCESSED / clave / f"{fecha}.nc"
            if not ruta.exists():
                continue
            ds = xr.open_dataset(ruta)
            agua = np.isfinite(ds["cyano"].values)
            filas.append({
                "lago": clave, "fecha": fecha,
                "cyano": float(np.nanmean(ds["cyano"].values)),
                "ndvi": float(np.nanmean(ds["ndvi"].values[agua])),
                "ndwi": float(np.nanmean(ds["ndwi"].values[agua])),
            })
    return pd.DataFrame(filas)


def scatter_medias(df: pd.DataFrame):
    """Scatter NDVI/NDWI vs NDCI (una media por fecha), con ajuste lineal."""
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    colores = {"atitlan": "#1f78b4", "amatitlan": "#e31a1c"}
    for ax, indice in zip(axes, ("ndvi", "ndwi")):
        for clave, lago in LAGOS.items():
            sub = df[df["lago"] == clave]
            ax.scatter(sub[indice], sub["cyano"], color=colores[clave],
                       label=lago["nombre"], alpha=0.85)
            if len(sub) > 2:
                m, b = np.polyfit(sub[indice], sub["cyano"], 1)
                xs = np.linspace(sub[indice].min(), sub[indice].max(), 20)
                ax.plot(xs, m * xs + b, color=colores[clave], ls="--", alpha=0.6)
        ax.set_xlabel(f"{indice.upper()} medio sobre el agua")
        ax.set_ylabel("NDCI medio (cianobacteria)")
        ax.grid(alpha=0.3)
        ax.legend()
    fig.suptitle("Relación de NDVI y NDWI con el índice de cianobacteria "
                 "(una media por fecha)")
    fig.tight_layout()
    FIGURAS.mkdir(parents=True, exist_ok=True)
    salida = FIGURAS / "correlacion_medias.png"
    fig.savefig(salida, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return salida


def interpretar(corr: pd.DataFrame):
    """Resumen por lago e índice: signo y fuerza promedio de la correlación."""
    print("\nCorrelación promedio (Pearson) por lago e índice:")
    for (clave, indice), grupo in corr.groupby(["lago", "indice"]):
        r = grupo["pearson_r"].mean()
        fuerza = ("fuerte" if abs(r) >= 0.6 else
                  "moderada" if abs(r) >= 0.3 else "débil")
        signo = "positiva" if r > 0 else "negativa"
        print(f"  {LAGOS[clave]['nombre']:<20} {indice.upper()}: "
              f"r̄={r:+.3f} ({signo}, {fuerza})")


def main():
    filas = []
    for clave, lago in LAGOS.items():
        filas += correlacion_pixel(clave, lago)
    corr = pd.DataFrame(filas)
    if corr.empty:
        print("⚠ sin índices procesados; correr antes 02_indices.py")
        return
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    salida = DATA_PROCESSED / "correlaciones.csv"
    corr.to_csv(salida, index=False)
    print(f"✓ correlaciones por fecha -> {salida.name}")

    png = scatter_medias(medias_por_fecha())
    print(f"✓ scatter de medias -> {png.name}")
    interpretar(corr)


if __name__ == "__main__":
    main()
